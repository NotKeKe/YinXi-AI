import discord
from discord import app_commands, Interaction
from discord.ext import commands
from typing import Optional

from core.functions import create_basic_embed, testing_guildID
from core.classes import Cog_Extension
from core.translator import load_translated, locale_str

from cmds.ai_chat.utils.auto_complete import custom_user_system_prompt_for_del
from cmds.ai_chat.utils.prompt import upload_custom_system_prompt, in_custom_system_prompt, delete_custom_system_prompt

class SystemPrompt(Cog_Extension):
    async def cog_load(self):
        print(f'已載入{__name__}')

    @commands.hybrid_command(name=locale_str('system_prompt_description'), description=locale_str('system_prompt_description'))
    async def system_prompt_description(self, ctx: commands.Context):
        '''i18n'''
        eb = load_translated(await ctx.interaction.translate('embed_system_prompt_description'))[0]
        author = eb.get('author')
        description = eb.get('description')
        ''''''
        eb = create_basic_embed(description=description, 功能=author, time=False)
        await ctx.send(embed=eb)

    @commands.hybrid_command(name=locale_str('upload_custom_system_prompt'), description=locale_str('upload_custom_system_prompt'))
    async def _upload_custom_system_prompt(self, ctx: commands.Context, name: str, text: Optional[str] = None, file: Optional[discord.Attachment] = None):
        if not text and not file: return await ctx.send(await ctx.interaction.translate('send_upload_custom_system_prompt_select_one_upload'))
        if text and file: return await ctx.send(await ctx.interaction.translate('send_upload_custom_system_prompt_select_one_upload'))
        if (await in_custom_system_prompt(ctx.author.id, name)): return await ctx.send(await ctx.interaction.translate('send_upload_custom_system_prompt_name_exist'))

        if file:
            content = (await file.read()).decode('utf-8')
        else:
            content = text

        await upload_custom_system_prompt(ctx.author.id, name, content)

        '''i18n'''
        eb = load_translated(await ctx.interaction.translate('embed_upload_custom_system_prompt'))[0]
        author = eb.get('author')
        ''''''

        eb = create_basic_embed(title=name, description=content[:3500], 功能=author)

        await ctx.send(embed=eb)

    @commands.hybrid_command(name=locale_str('delete_custom_system_prompt'), description=locale_str('delete_custom_system_prompt'))
    @app_commands.autocomplete(name=custom_user_system_prompt_for_del)
    async def _delete_custom_system_prompt(self, ctx: commands.Context, name: str):
        if not (await in_custom_system_prompt(ctx.author.id, name)): return await ctx.send(await ctx.interaction.translate('send_delete_custom_system_prompt_name_not_exist'))
        await delete_custom_system_prompt(ctx.author.id, name)

        await ctx.send(await ctx.interaction.translate('send_delete_custom_system_prompt_success'))

    @app_commands.command(name='預設提示詞插入')
    @app_commands.guilds(discord.Object(testing_guildID))
    async def _insert_default_system_prompt(self, inter: Interaction, file: discord.Attachment):
        await inter.response.defer()

        name = file.filename.split('.')[0]

        from core.functions import mongo_db_client
        content = (await file.read()).decode('utf-8')
        client = mongo_db_client['system_prompt']['default']

        await client.insert_one({'name': name, 'prompt': content.strip()})

        await inter.followup.send('success')

async def setup(bot):
    await bot.add_cog(SystemPrompt(bot))