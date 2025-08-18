from discord.ext import commands
from discord import app_commands, Interaction

from core.classes import Cog_Extension
from core.functions import create_basic_embed
from core.translator import locale_str
from cmds.ai_chat.chat.translate import translate

class Translator(Cog_Extension):
    async def cog_load(self):
        print(f'已載入「{__name__}」')

    @commands.hybrid_command(name=locale_str('translate'), description=locale_str('translate'))
    @app_commands.describe(content=locale_str('translate_content'), target=locale_str('translate_target'))
    async def translate(self, ctx: commands.Context, content: str, target:str = 'zh-TW'):
        async with ctx.typing():
            translated = await translate(content, target, ctx.interaction.locale.value)
            
            embed = create_basic_embed(description=translated, color=ctx.author.color)
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
            embed.set_footer(text='Powered by qwen-3-235b-a22b-instruct-2507')

            await ctx.send(embed=embed)

    @app_commands.command(name=locale_str('translate_from_message'), description=locale_str('translate_from_message'))
    @app_commands.describe(to_lang=locale_str('translate_from_message_to_lang'))
    async def _translate_from_message(self, inter: Interaction, msg_id: str, to_lang: str = None):
        await inter.response.defer(ephemeral=True, thinking=True)

        try: msg_id = int(msg_id)
        except: return await inter.followup.send(await inter.translate('translate_from_message_invaild_msgid'))

        msg = await inter.channel.fetch_message(msg_id)
        if not msg: return await inter.followup.send(await inter.translate('translate_from_message_no_msg_found'))
        if not msg.content: return await inter.followup.send(await inter.translate('translate_from_message_no_content_found'))

        translated = await translate(msg.content, to_lang or inter.locale.value, inter.locale.value)

        eb = create_basic_embed(description=translated, color=inter.user.color)
        eb.set_author(name=msg.author.name, icon_url=msg.author.avatar.url)
        eb.set_footer(text='Powered by qwen-3-235b-a22b-instruct-2507')
        await inter.followup.send(embed=eb, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Translator(bot))