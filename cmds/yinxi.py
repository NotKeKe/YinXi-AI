import discord
from discord.ui import Button, View
from discord.ext import commands, tasks
import asyncio
from datetime import timedelta, timezone

from cmds.ai_chat.on_msg.yinxi import YinXiRun
from cmds.vector.call.call import upsert

from core.functions import testing_guildID, create_basic_embed
from core.mongodb_clients import MongoDB_DB
from core.qdrant import QdrantCollectionName
from core.translator import locale_str, load_translated

async def is_enable_YinXi_chat(userID: int) -> bool:
    collection = MongoDB_DB.yinxi_chat['config']
    result = await collection.find_one({'userID': userID})
    return result.get('enable_history_collect', False) if result else False

class YinXi(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        self.bot = bot
        self.running_client: dict[int, YinXiRun] = {}

    async def cog_load(self):
        print(f'已載入「{__name__}」')

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        await self.on_msg_chat(msg)

    async def on_msg_chat(self, msg: discord.Message):
        if not msg.content: return
        if not msg.guild == testing_guildID: return
        if msg.author.bot: return

        client = self.running_client.get(msg.channel.id)
        if client:
            client.task.cancel()

        client = client or YinXiRun(await self.bot.get_context(msg))
        self.running_client[msg.channel.id] = client
        await client.run()
        del self.running_client[msg.channel.id]

    async def on_msg_to_vector_history(self, msg: discord.Message):
        if not msg.content: return
        if not (await is_enable_YinXi_chat(msg.author.id)): return
        await upsert(
            data=[{
                'channelID': msg.channel.id,
                'userID': msg.author.id,
                'userName': msg.author.global_name,
                'messageID': msg.id,
                'time': msg.created_at.astimezone(timezone(timedelta(hours=8))).strftime("%Y/%m/%d %H:%M:%S"),
                'text': msg.content
            }],
            collection_name=QdrantCollectionName.yinxi_passed_history
        )

    @commands.hybrid_command(name=locale_str('yinxi_chat_command'), description=locale_str('yinxi_chat_command'))
    async def yinxi_chat_enable_history_collect(self, ctx: commands.Context):
        async def button_check_callback(inter: discord.Interaction):
            collection = MongoDB_DB.yinxi_chat['config']
            await collection.update_one(
                {'userID': ctx.guild.id},
                {'$set': {'enable_history_collect': True}},
                upsert=True
            )
            await ctx.send((await ctx.interaction.translate('send_yinxi_chat_command')).format(enable=True))
        async def button_refuse_callback(inter: discord.Interaction):
            collection = MongoDB_DB.yinxi_chat['config']
            await collection.update_one(
                {'userID': ctx.guild.id},
                {'$set': {'enable_history_collect': False}},
                upsert=True
            )
            await ctx.send((await ctx.interaction.translate('send_yinxi_chat_command')).format(enable=False))

        button_check = Button(style=discord.ButtonStyle.blurple, label='Accept', emoji='✅')
        button_refuse = Button(style=discord.ButtonStyle.red, label='Refuse', emoji='❌')

        button_check.callback = button_check_callback
        button_refuse.callback = button_refuse_callback

        view = View()
        view.add_item(button_check)
        view.add_item(button_refuse)

        '''i18n'''
        eb_text = load_translated(await ctx.interaction.translate('embed_yinxi_chat_command'))[0]
        title = eb_text.get('title')
        descrip = eb_text.get('description')
        ''''''

        eb = create_basic_embed(title, descrip)
        await ctx.send(view=view, embed=eb)

async def setup(bot):
    await bot.add_cog(YinXi(bot))