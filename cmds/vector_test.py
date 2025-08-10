import discord
from discord import app_commands, Interaction
from discord.ext import commands, tasks
import aiohttp

from core.classes import Cog_Extension
from core.functions import testing_guildID

from cmds.vector.call import search, upsert
from cmds.vector.utils.config import (
    connection as vector_connection,
    CollectionName
)
from cmds.vector.utils import check_alive

class VectorTest(Cog_Extension):
    def __init__(self, bot):
        super().__init__(bot)
        self.session: aiohttp.ClientSession | None = None

    async def cog_load(self):
        print(f'已載入「{__name__}」')
        self.session = aiohttp.ClientSession()
        self.ollama_check_alive.start()
        await vector_connection()

    async def cog_unload(self):
        if self.session and not self.session.closed:
            await self.session.close()

    @app_commands.command(name='向量測試搜尋')
    async def vector_test_search(self, inter: Interaction, query: str):
        await inter.response.defer(ephemeral=True, thinking=True)

        result = await search(query, CollectionName.databases)
        if not result: return await inter.followup.send('No result')
        await inter.followup.send(str(result))

    @app_commands.command(name='向量測試插入')
    async def vector_test_insert(self, inter: Interaction):
        await inter.response.defer(ephemeral=True, thinking=True)

        upsert_item = [
            {
                'text': '早安',
                'userID': inter.user.id
            },
            {
                'text': '世界計劃是一個音樂遊戲',
                'userID': inter.user.id
            }
        ]

        status = await upsert(upsert_item, CollectionName.databases)
        await inter.followup.send(f'插入 {status}')

    @tasks.loop(seconds=60)
    async def ollama_check_alive(self):
        await check_alive.connection_check(self.session)

    @ollama_check_alive.before_loop
    async def before_test_loop(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(VectorTest(bot))