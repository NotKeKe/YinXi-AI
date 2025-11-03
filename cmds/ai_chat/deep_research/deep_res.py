import discord
from discord.ext import commands

from ..utils.client import AsyncClient

from .new_question import NewQuestion
from .sub_questions import SubQuestions
from .gener_keywords import GenerKeywords
from .search import Search

from .information import Info
from .utils import *

class DeepResearcher:
    def __init__(self, ctx: commands.Context, init_question: str):
        self.init_question = init_question

        self.info = Info(ctx) # collect information
        self.client = AsyncClient.lmstudio # ai client

    async def run(self):
        self.info.curr_states = 'init'
        await send_message(self.info, 'Initializing, Please wait...')

        # 詢問使用者新問題，回傳答案
        self.info.curr_states = 'ask_new_question'
        await NewQuestion(self.info, self.init_question).run()

        # 生成子問題
        self.info.curr_states = 'gener_sub_questions'
        await SubQuestions(self.info).run()

        # 對每個子問題 生成 keywords
        self.info.curr_states = 'gener_keywords'
        await GenerKeywords(self.info).run()

        # search
        self.info.curr_states = 'search'
        await Search(self.info).run()

        # summary search results
        self.info.curr_states = 'summary'
        