from discord.ext import commands, tasks
from pathlib import Path
import aiofiles
from datetime import datetime, timedelta, timezone
import logging
import time

from core.classes import Cog_Extension
from core.functions import create_basic_embed
from core.translator import locale_str, load_translated

from cmds.daily_rag.main import daily_rag
from cmds.daily_rag.tests.ask_ai import ask_ai

RECORD_FILE_PATH = Path.cwd() / 'cmds' / 'daily_rag' / 'last_rag_time.txt'
RECORD_FILE_PATH.touch(exist_ok=True)

logger = logging.getLogger(__name__)

class DailyRag(Cog_Extension):
    def __init__(self, bot):
        super().__init__(bot)
    
    async def cog_load(self):
        print(f'已載入「{__name__}」')
        self.daily_rag_task.start()

    async def cog_unload(self):
        self.daily_rag_task.stop()

    @commands.hybrid_command(name=locale_str("daily_rag_search"), description=locale_str("daily_rag_search"))
    async def daily_rag_search(self, ctx: commands.Context, query: str, with_ai: bool = False):
        await ctx.defer()
        resp = await ask_ai(query)
        await ctx.send(resp) # type: ignore

    @tasks.loop(hours=24)
    async def daily_rag_task(self):
        try:
            async with aiofiles.open(RECORD_FILE_PATH, 'r', encoding='utf-8') as f:
                last_rag_time = await f.read() or '1999-11-11T11:11:11+00:00'
        except:
            last_rag_time = '1999-11-11T11:11:11+00:00'

        if (
            datetime.fromisoformat(last_rag_time).strftime('%Y-%m-%d') # date from file
            ==
            datetime.now().astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d') # curr date
        ):
            return

        start_time = time.time()

        logger.info('Running Daily Rag')
        await daily_rag()

        async with aiofiles.open(RECORD_FILE_PATH, 'w', encoding='utf-8') as f:
            await f.write(datetime.now().astimezone(timezone(timedelta(hours=8))).isoformat())

        logger.info(f'Finished Daily Rag in {round(time.time() - start_time, 2)}s')

    @daily_rag_task.before_loop
    async def before_daily_rag_task(self):
        ...

async def setup(bot):
    await bot.add_cog(DailyRag(bot))