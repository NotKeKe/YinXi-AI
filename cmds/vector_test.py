import discord
from discord import app_commands, Interaction
from discord.ext import commands

from core.classes import Cog_Extension
from core.functions import testing_guildID

from vector.call import search, insert
from vector.utils.config import connection as vector_connection
from vector.utils import connection_check

class VectorTest(Cog_Extension):
    async def cog_load(self):
        print(f'已載入「{__name__}」')

    @app_commands.command(name='向量測試搜尋')
    async def vector_test_search(self, inter: Interaction, query: str):
        await inter.response.defer(ephemeral=True, thinking=True)

        result = await search(query)
        await inter.followup.send('\n'.join(result))

    @app_commands.command(name='向量測試插入')
    async def vector_test_insert(self, inter: Interaction, query: str):
        await inter.response.defer(ephemeral=True, thinking=True)

        await insert(query)
        await inter.followup.send('插入成功')


async def setup(bot):
    await bot.add_cog(VectorTest(bot))