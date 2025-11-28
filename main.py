import discord
from discord.ext import commands
import json
import os
from dotenv import load_dotenv
import asyncio
import time
import traceback
import logging
import sys

from core.functions import math_round, current_time, testing_guildID
from core.translator import i18n, MockInteraction
from core.setup_log import setup_logging, StreamToLogger
from core.classes import set_bot

# get env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
KeJC_ID = int(os.getenv('KeJC_ID'))
embed_link = os.getenv('embed_default_link')
online_time = None
start_time = time.time()

# log setup
setup_logging()
root_logger = logging.getLogger()
sys.stdout = StreamToLogger(root_logger, logging.INFO)
sys.stderr = StreamToLogger(root_logger, logging.ERROR)
root_logger.info('輸出已被重導向至 `/logs`')

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
# intents.presences = True


bot = commands.Bot(command_prefix=']', intents=intents)
set_bot(bot)

# Bot's help default command
ending_note = "這是 {ctx.bot.user.name} 的commands help\n輸入 {help.clean_prefix}{help.invoked_with} 或是 [helping 來尋求幫助"
bot.help_command = None

@bot.event
async def setup_hook():
    try:
        translator = i18n()
        await bot.tree.set_translator(translator)
        synced_bot_guild = await bot.tree.sync(guild=discord.Object(id=testing_guildID))
        synced_bot = await bot.tree.sync()
        print(f'Synced {len(synced_bot + synced_bot_guild)} commands.')
    except Exception as e:
        print("出錯 when synced: ", e)

    global online_time
    online_time = current_time()
    
@bot.before_invoke
async def before_invoke(ctx: commands.Context):
    """
    在任何指令執行前被呼叫，用於填充 ctx.interaction。
    """
    if ctx.interaction is None:  
        try:
            ctx.interaction = MockInteraction(ctx)
        except:
            traceback.print_exception()

# 錯誤追蹤
@bot.event
async def on_command_error(ctx, error):
    if ctx.command is None: return
    await ctx.invoke(bot.get_command('errorresponse'), 檔案名稱=__name__, 指令名稱=ctx.command.name, exception=error, user_send=False, ephemeral=True)

#上線通知
@bot.event
async def on_ready():
    print('我上線了窩\n')

#讓私訊也能被處理
@bot.event
async def on_message(message):
    # 忽略機器人自己的消息
    if message.author == bot.user:
        return

    # 處理私訊中的指令
    if isinstance(message.channel, discord.DMChannel):
        await bot.process_commands(message)
    else:
        # 處理伺服器中的指令
        await bot.process_commands(message)

async def load():
    for filename in os.listdir('./cmds'):
        now = time.time()
        try:
            if filename.endswith('.py'):
                await bot.load_extension(f'cmds.{filename[:-3]}')
                print(f'嘗試載入cmds.{filename} (cost: {math_round(time.time()-now, 2)})')
        except commands.errors.NoEntryPointError:
            root_logger.warning(f"cmds.{filename} has not 'setup' function. (cost: {math_round(time.time()-now, 2)})")
        except Exception as e:
            # traceback.print_exc()
            root_logger.warning(f'出錯 When loading extension: {e} (cost: {math_round(time.time()-now, 2)})', exc_info=True)
    
        
async def main():
    async with bot:
        await load()
        print(f'開啟共花費了: {math_round(time.time() - start_time, 2)}')
        await bot.start(TOKEN)

async def cleanup():
    from core.functions import mongo_db_client
    if mongo_db_client:
        mongo_db_client.close()
        
    from core.chat_human.manage_browser import close_browser
    await close_browser()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        asyncio.run(cleanup())