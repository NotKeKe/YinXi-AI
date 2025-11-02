from .utils import *
from typing import TYPE_CHECKING, Any
import orjson
from collections.abc import Iterable

if TYPE_CHECKING:
    from .information import Info

SYSTEM_PROMPT = '''
你是一個專業資料搜尋專家
根據以下研究子問題，產生 5 條以上的高品質搜尋關鍵字（可直接用於網頁搜尋）。

輸出格式:
['KEYWORD 1', 'KEYWORD 2'...]
'''.strip()

class GenerKeywords:
    def __init__(self, info: 'Info'):
        self.info = info

    def _format_list(self, text: str) -> list[str] | str:
        '''return list[str] or str, if returned str, it means error accured'''
        try:
            result = orjson.loads(text.strip())
        except orjson.JSONDecodeError:
            return 'Json Decode Error, please try again according to the rules'

        if not isinstance(result, Iterable):
            return f'You must output a list[str], not {type(result)}'
        
        if isinstance(result, Iterable) and not isinstance(result, list): # 是 iterable，但不是 list
            result = list(result)

        if not all(isinstance(item, str) for item in result):
            return 'You must output a list[str], not a list of other types'
        
        return result

    async def gener_keywords(self):
        '''為單個問題生成 keywords'''
        messages = [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': f'Main Question: {self.info.init_question}\n{self.info.detail_questions}'}
        ]
        result: Any = None

        while not isinstance(result, list): # 自動錯誤重試
            resp = await self.info.client.chat.completions.create(
                model=self.info.model,
                messages=messages, # type: ignore
                temperature=0.5
            )

            output_result = resp.choices[0].message.content
            result = self._format_list(str(output_result))

            messages.extend([{'role': 'assistant', 'content': str(output_result)}, {'role': 'user', 'content': result}])

        return result

    async def run(self):
        keywords = {}
        for q in self.info.sub_questions or []:
            keywords[q] = await self.gener_keywords()
        self.info.keywords = keywords