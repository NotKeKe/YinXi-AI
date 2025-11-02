import discord
from discord.ext import commands
import orjson
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

from core.classes import get_bot

from .utils import *

if TYPE_CHECKING:
    from .information import Info

SYSTEM_PROMPT = '''
你是一位研究助理，現在使用者的問題仍然有點模糊，你需要詢問更多的資訊來確保最終的回答符合使用者的預期。
請根據使用者的問題，詢問更多資訊，最少詢問3個。
確保不要輸出任何 markdown 格式。

輸出格式:
['QUESTION 1', 'QUESTION 2'...]
'''.strip()

class NewQuestion:
    def __init__(self, info: 'Info', init_question: str):
        self.init_question = init_question
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

    async def ask_question(self) -> list[str]:
        # generate new questions, 1~5
        messages = [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': f'Question: {self.init_question}'}
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
        # generate new questions
        new_questions = await self.ask_question()
        self.info.new_questions = new_questions
        assert self.info.msg is not None
        await edit_message(self.info, f'Please reply this message, and answer the following questions to help me clarify your question:\n {"\n".join(f"{i+1}. {q}" for i, q in enumerate(new_questions))}', tag_user=True)

        # 等待使用者回覆
        bot = get_bot()
        reply = await bot.wait_for(
            'message', 
            check=lambda m: m.author == self.info.ctx.author and m.channel == self.info.ctx.channel
        ) # 檢查 使用者是否跟初始訊息相同，頻道是否相同

        self.info.new_questions_answer = reply.content

        await send_message(self.info, 'Already got your answer!', save_to_info=False)