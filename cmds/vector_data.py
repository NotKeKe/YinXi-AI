import discord
from discord import app_commands, Interaction
from discord.ext import commands, tasks
from datetime import datetime
import uuid
import orjson
import logging
from qdrant_client.models import Filter, MatchValue, FieldCondition, ScrollResult

from core.classes import Cog_Extension
from core.functions import testing_guildID, redis_client, UnixToReadable, create_basic_embed
from core.translator import locale_str, load_translated

from core.mongodb_clients import MongoDB_DB
from core.qdrant import QdrantCollectionName

from cmds.vector.call import search, upsert, delete, show
from cmds.vector.utils.config import (
    connection as vector_connection,
    CollectionName
)
from cmds.vector.utils import check_alive, semantic_split
from cmds.vector.utils.autocomplete import *

logger = logging.getLogger(__name__)

class VectorData(Cog_Extension):
    def __init__(self, bot):
        super().__init__(bot)

    async def cog_load(self):
        print(f'已載入「{__name__}」')
        self.ollama_check_alive.start()
        await vector_connection()

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        await self.on_msg_chat_human_embedding(msg)

    async def on_msg_chat_human_embedding(self, msg: discord.Message):
        if not msg.content: return
        if msg.author.bot and msg.author != self.bot.user: return
        if msg.content.startswith(']') or msg.content.startswith(']! '): return
        if len(msg.content) <= 2: return

        # to check whether the channel is a chat_human channel (if not in DM). Always do embed for DM.
        if msg.guild:
            db = MongoDB_DB.chat_human_setting
            collection = db[str(msg.channel.id)]

            init_data = await collection.find_one({'_id': 'chat_human_setting'})
            if not init_data: return

        name = 'chat_human_embedding'
        key = str(msg.channel.id)

        ls_msgs = await redis_client.hget(name, str(msg.channel.id))
        set_item = [{'userID': str(msg.author.id), 'userName': str(msg.author.name), 'text': msg.content}]

        if not ls_msgs: 
            dump_item = set_item
        else:
            ls_msgs = orjson.loads(ls_msgs)
            if len(ls_msgs) >= 10:
                await upsert(
                    [{'userID': int(item.get('userID', 0)), 'userName': str(item.get('userName', '')), 'text': item.get('text', '')} for item in ls_msgs],
                    QdrantCollectionName.chat_human_history
                )
                await redis_client.hdel(name, key)
                logger.info(f'Add {len(ls_msgs)} items to Qdrant')
                dump_item = set_item
            else:
                dump_item = ls_msgs + set_item

        await redis_client.hset(name, key, orjson.dumps(dump_item).decode())
        logger.info(f'Add {len(dump_item)} items to Redis')

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

    @app_commands.command(name=locale_str('custom_vector_database_upload'), description=locale_str('custom_vector_database_upload'))
    @app_commands.describe(file=locale_str('custom_vector_database_upload_file'), title=locale_str('custom_vector_database_upload_title'))
    async def vector_test_add_file(self, inter: Interaction, file: discord.Attachment, title: str):
        await inter.response.defer(ephemeral=True, thinking=True)

        if not file.filename.endswith('.txt') and not file.filename.endswith('.md'): return await inter.followup.send(await inter.translate('send_custom_vector_database_upload_invalid_file_format'))

        # uuid
        u = str(uuid.uuid4())

        # vector
        texts = semantic_split((await file.read()).decode('utf-8'))
        upsert_item = [{'userID': inter.user.id, 'text': t, 'uuid': u} for t in texts]
        success = await upsert(upsert_item, CollectionName.user_custom_database)

        # Mongo
        db = MongoDB_DB.user_custom_data
        collection = db[str(inter.user.id)]
        await collection.insert_one({'uuid': u, 'title': title, 'length': len(upsert_item)})

        await inter.followup.send((await inter.translate('send_custom_vector_database_upload_success')).format(filename=file.filename))

    @app_commands.command(name=locale_str('custom_vector_database_search'), description=locale_str('custom_vector_database_search'))
    @app_commands.autocomplete(database=custom_database_titles)
    @app_commands.describe(query=locale_str('custom_vector_database_search_query'))
    async def vector_test_search_custom(self, inter: Interaction, query: str, database: str):
        await inter.response.defer(ephemeral=True, thinking=True)

        result = await search(
            query, 
            CollectionName.user_custom_database, 
            Filter(must=[
                FieldCondition(key='userID', match=MatchValue(value=inter.user.id)),
                FieldCondition(key='title', match=MatchValue(value=database))
            ]
        ))
        if not result: return await inter.followup.send('No result')

        eb = create_basic_embed(title='Search results', description=orjson.dumps(result, option=orjson.OPT_INDENT_2).decode('utf-8'))

        await inter.followup.send(embed=eb)

    @app_commands.command(name=locale_str('custom_vector_database_rename'), description=locale_str('custom_vector_database_rename'))
    @app_commands.autocomplete(original_database_name=custom_database_titles)
    async def vector_test_rename_custom(self, inter: Interaction, original_database_name: str, new_name: str):
        await inter.response.defer(ephemeral=True, thinking=True)

        # Mongo
        mongo_collection = MongoDB_DB.user_custom_data[str(inter.user.id)]
        await mongo_collection.find_one_and_update({'title': original_database_name}, {'$set': {'title': new_name}})
        
        await inter.followup.send((await inter.translate('send_custom_vector_database_rename_success')).format(original_name=original_database_name, new_name=new_name))

    @app_commands.command(name=locale_str('custom_vector_database_delete'), description=locale_str('custom_vector_database_delete'))
    @app_commands.autocomplete(database=custom_database_titles)
    @app_commands.describe(database=locale_str('custom_vector_database_delete_database'))
    async def vector_test_delete_custom(self, inter: Interaction, database: str):
        await inter.response.defer(ephemeral=True, thinking=True)

        # Mongo
        mongo_collection = MongoDB_DB.user_custom_data[str(inter.user.id)]
        doc = await mongo_collection.find_one_and_delete({'title': database})

        # Qdrant
        condition = Filter(
            must=[
                FieldCondition(
                    key='userID', match=MatchValue(value=inter.user.id)
                ),
                FieldCondition(
                    key='uuid', match=MatchValue(value=doc['uuid'])
                )
            ]
        )
        await delete(CollectionName.user_custom_database, condition)
        
        await inter.followup.send((await inter.translate('send_custom_vector_database_delete_success')).format(name=database))

    @commands.hybrid_command(name=locale_str('show_long_term_memory'), description=locale_str('show_long_term_memory'))
    async def _show_long_term_memory(self, ctx: commands.Context):
        async with ctx.typing():
            ft = Filter(
                must=[
                    FieldCondition(key='userID', match=MatchValue(value=ctx.author.id))
                ]
            )
            results: list = await show(QdrantCollectionName.user_long_term_memory, ft)

            '''i18n'''
            eb = load_translated(await ctx.interaction.translate('embed_show_long_term_memory'))[0]
            title = eb.get('title')
            ''''''

            eb = create_basic_embed(title=title, description='\n'.join([f'{i+1}. {item.get('text')} ({UnixToReadable(item.get("time", 0))})' for i, item in enumerate(results)]))
            await ctx.send(embed=eb)

    @commands.hybrid_command(name=locale_str('add_long_term_memory'), description=locale_str('add_long_term_memory'))
    async def _add_long_term_memory(self, ctx: commands.Context, text: str):
        async with ctx.typing():
            status = await upsert(
                [{'text': text, 'userID': ctx.author.id, 'time': datetime.now().timestamp()}],
                QdrantCollectionName.user_long_term_memory
            )

            await ctx.send((await ctx.interaction.translate('send_add_long_term_memory_succeeded')).format(text=text) if status else (await ctx.interaction.translate('send_add_long_term_memory_failed')).format(text=text))

    @commands.hybrid_command(name=locale_str('clear_long_term_memory'), description=locale_str('clear_long_term_memory'))
    async def _clear_long_term_memory(self, ctx: commands.Context):
        async with ctx.typing():
            view = discord.ui.View()
            button_check = discord.ui.Button(label='Yes', emoji='✅', style=discord.ButtonStyle.blurple)
            button_cancel = discord.ui.Button(label='No', emoji='❌', style=discord.ButtonStyle.blurple)

            async def button_check_callback(inter: Interaction):
                msg = inter.message
                await inter.response.defer(ephemeral=True, thinking=True)

                ft = Filter(
                    must=[FieldCondition(key='userID', match=MatchValue(value=ctx.author.id))]
                )
                await delete(QdrantCollectionName.user_long_term_memory, ft)

                await inter.followup.send((await ctx.interaction.translate('send_clear_long_term_memory_succeeded')), ephemeral=True)
                await msg.edit(view=None)

            async def button_cancel_callback(inter: Interaction):
                msg = inter.message
                await inter.response.defer(ephemeral=True, thinking=True)
                await inter.followup.send(await ctx.interaction.translate('send_clear_long_term_memory_canceled'), ephemeral=True)
                await msg.edit(view=None)

            button_check.callback = button_check_callback
            button_cancel.callback = button_cancel_callback

            view.add_item(button_check)
            view.add_item(button_cancel)

            '''i18n'''
            eb = load_translated(await ctx.interaction.translate('embed_clear_long_term_memory_confirm'))[0]
            title = eb.get('title')
            ''''''

            eb = create_basic_embed(title)

            await ctx.send(embed=eb, view=view)

    @commands.command(name='ollama_check_alive')
    async def _ollama_check_alive(self, ctx: commands.Context):
        await ctx.send(await check_alive.get_connection_status())
        await ctx.send(await redis_client.get('lmstudio_is_connected'))

    @tasks.loop(seconds=60)
    async def ollama_check_alive(self):
        await check_alive.connection_check()

    @ollama_check_alive.before_loop
    async def before_test_loop(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(VectorData(bot))