import discord
from discord import app_commands, Interaction
from discord.ext import commands, tasks
import aiohttp
import uuid
import orjson
from qdrant_client.models import Filter, MatchValue, FieldCondition

from core.classes import Cog_Extension
from core.functions import testing_guildID, mongo_db_client

from cmds.vector.call import search, upsert
from cmds.vector.utils.config import (
    connection as vector_connection,
    CollectionName
)
from cmds.vector.utils import check_alive, split_str_by_len

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
    @app_commands.guilds(discord.Object(id=testing_guildID))
    async def vector_test_search(self, inter: Interaction, query: str):
        await inter.response.defer(ephemeral=True, thinking=True)

        result = await search(query, CollectionName.databases)
        if not result: return await inter.followup.send('No result')
        await inter.followup.send(str(result))

    @app_commands.command(name='向量測試插入')
    @app_commands.guilds(discord.Object(id=testing_guildID))
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

    @app_commands.command(name='向量加入知識庫')
    @app_commands.guilds(discord.Object(id=testing_guildID))
    async def vector_test_add_file(self, inter: Interaction, file: discord.Attachment, title: str):
        await inter.response.defer(ephemeral=True, thinking=True)
        # await inter.followup.send(file.filename)
        if not file.filename.endswith('.txt') and not file.filename.endswith('.md'): return await inter.followup.send('目前僅支援 txt(文字檔案)與 md(markdown) 格式的資料窩')

        # uuid
        u = str(uuid.uuid4())

        # Mongo
        db = mongo_db_client['user_custom_data']
        collection = db[str(inter.user.id)]
        await collection.insert_one({'uuid': u, 'title': title})

        # vector
        texts = split_str_by_len((await file.read()).decode('utf-8'))
        upsert_item = [{'title': title, 'userID': inter.user.id, 'text': t, 'uuid': u} for t in texts]
        success = await upsert(upsert_item, CollectionName.user_custom_database)

        if not success: 
            await collection.delete_one({'uuid': u})
            return await inter.followup.send('插入失敗')
        await inter.followup.send('插入成功')

    @app_commands.command(name='向量自定義知識庫查詢')
    @app_commands.guilds(discord.Object(id=testing_guildID))
    async def vector_test_search_custom(self, inter: Interaction, query: str):
        await inter.response.defer(ephemeral=True, thinking=True)

        result = await search(query, CollectionName.user_custom_database, Filter(must=[FieldCondition(key='userID', match=MatchValue(value=inter.user.id))]))
        if not result: return await inter.followup.send('No result')

        await inter.followup.send(orjson.dumps(result, option=orjson.OPT_INDENT_2).decode('utf-8'))

    @tasks.loop(seconds=60)
    async def ollama_check_alive(self):
        await check_alive.connection_check(self.session)

    @ollama_check_alive.before_loop
    async def before_test_loop(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(VectorTest(bot))