from typing import Literal
import discord
from discord.ext import commands
from openai import AsyncOpenAI
import asyncio
from textwrap import dedent

from ..utils.client import AsyncClient
from .utils import *

states_type = Literal['init', 'ask_new_question', 'answer_new_question', 'gener_sub_questions', 'gener_keywords', 'search', 'summary', 'reflection', 'summary_all', 'check']
'''
(一)
init: 初始化
ask_new_question: 問使用者 new_question
answer_new_question: 使用者回答 new_question
(二)
gener_sub_questions: AI 生成多個子問題
gener_keywords: AI 針對每個子問題，生成多個 keywords。用於查詢
search: 搜尋。搜尋完成後透過 embedding 暫存。 <--- 需針對每個子問題分塊
summary: AI 重新整理搜尋結果 <---- 針對每個子問題整理
(三)
reflection: AI 針對搜尋結果進行反思。讓AI找出缺漏的面向。 <--- 有可能需要再執行 (二)
(四)
summary_all: 整合全部的 summary，並產出報告
(五)
check: 檢查產出的報告，如有需要，再次執行(三)
'''

class Info:
    def __init__(self, ctx: commands.Context):
        self.ctx: commands.Context = ctx
        self.msg: discord.Message | None = None
        self.status_msg: discord.Message | None = None
        self.client: AsyncOpenAI = self.get_client()
        self.model: str = 'openai/gpt-oss-20b'
        self._curr_states: states_type | None = None

        # (一)
        self.init_question: str | None = None

        self.new_questions: list[str] | None = None
        self.new_questions_answer: str | None = None

        # (二)
        self._sub_questions: list[str] | None = None
        self.keywords: dict[str, list[str]] | None = None
        '''
        {
            sub_question: [keyword1, keyword2, ...]
        }
        '''

    def get_client(self):
        return AsyncClient.lmstudio
    
    @property
    def curr_states(self):
        return self._curr_states
    
    @curr_states.setter
    def curr_states(self, value: states_type):
        self._curr_states = value
        # 讓他傳送訊息 通知使用者現在的階段
        asyncio.create_task(send_message(self, f'curr_states: {value}')) 

    @property
    def detail_questions(self):
        return dedent(f'''
        Detail Questions:
        ```
        {"\n".join(f"{i+1}. {q}" for i, q in enumerate(self.new_questions or []))}
        ```

        Detail Answer:
        ```
        {self.new_questions_answer}
        ```
        ''').strip()
    
    @property
    def sub_questions(self):
        return self._sub_questions
    
    @sub_questions.setter
    def sub_questions(self, value: list[str] | None):
        self._sub_questions = value
        asyncio.create_task(send_message(self, f'Generated Sub Questions:\n```\n{"\n".join(value or [])}\n```', save_to_info=False))