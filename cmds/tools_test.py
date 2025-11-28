import discord
from discord import app_commands, Interaction
from discord.ext import commands
from asyncio import to_thread
import traceback
import io

from cmds.ai_chat.tools.map import tools
from cmds.ai_chat.utils import md_table_convert

from core.functions import testing_guildID, is_async
from core.classes import Cog_Extension

async def send(inter: Interaction, text: str) -> discord.File:
    if len(text) >= 2000:
        f = io.StringIO(text)
        file = discord.File(f, 'file.txt')
        await inter.followup.send(file=file)
    else:
        await inter.followup.send(text)

class ToolTest(Cog_Extension):
    async def cog_load(self):
        print(f'已載入「{__name__}」')

    @app_commands.command()
    @app_commands.guilds(discord.Object(id=testing_guildID))
    async def show_tools(self, inter: Interaction):
        await inter.response.send_message(', '.join(tools.keys()))

    @app_commands.command()
    @app_commands.guilds(discord.Object(id=testing_guildID))
    async def call_tools(self, inter: Interaction, function_name: str, args: str):
        try:
            await inter.response.defer()
            if function_name not in list(tools.keys()): return await inter.followup.send(f'`{function_name}` not found in tools map')

            func = tools[function_name]
            args = args.split()
            result = (await func(args)) if is_async(func) else (await to_thread(func, args))

            await send(inter, f'Result:\n```\n{result}\n```')
        except Exception as e:
            traceback.print_exc()
            await inter.followup.send(f'{function_name} failed run.\nReason: {str(e)}')

    @commands.command()
    async def convert_html_to_md(self, ctx: commands.Context, * , text: str):
        async with ctx.typing():
            result = await md_table_convert(text)
            file = io.BytesIO(result)
            file.seek(0)
            await ctx.send(file=discord.File(file, 'result.png'))


async def setup(bot):
    await bot.add_cog(ToolTest(bot))