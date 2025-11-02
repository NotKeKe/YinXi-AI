from typing import TYPE_CHECKING, Any
import orjson
from collections.abc import Iterable

from .utils import *

if TYPE_CHECKING:
    from .information import Info

SYSTEM_PROMPT = '''
你是一位研究助理，請針對使用者想要了解的問題，生成多個搜尋問題的可能方向。

輸出格式:
['QUESTION 1', 'QUESTION 2'...]
'''.strip()

class SubQuestions:
    '''
    此階段應該為使用者的初始問題，後續問題，生成多個問題方向，供後面生成 keywords
    '''
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
    
    async def gener_question(self) -> list[str]:
        # generate new questions, 1~5
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
        questions = await self.gener_question()
        self.info.sub_questions = questions