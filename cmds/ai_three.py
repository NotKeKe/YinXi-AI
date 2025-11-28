import discord
from discord import app_commands, Interaction
from discord.app_commands import Choice
from discord.ext import commands
import logging
from typing import Optional
import openai
import aiohttp
import io
from mutagen import File as MutagenFile
from datetime import datetime, timedelta, timezone
from bson import ObjectId
import asyncio
import orjson

from qdrant_client.models import Filter, MatchValue, FieldCondition

from core.functions import create_basic_embed, UnixNow, mongo_db_client, redis_client, OLLAMA_IP
from core.classes import Cog_Extension
from core.translator import locale_str, load_translated

from core.qdrant import QdrantCollectionName
from core.mongodb_clients import MongoDB_DB

from cmds.ai_chat.chat.chat import Chat
from cmds.ai_chat.chat import gener_title
from cmds.ai_chat.tools.map import image_generate, video_generate
from cmds.ai_chat.utils import model, add_history_button, add_think_button
from cmds.ai_chat.utils.auto_complete import chat_history_autocomplete, model_autocomplete, system_prompt_autocomplete
from cmds.ai_chat.utils.prompt import from_name_to_system_prompt

from cmds.vector.utils.autocomplete import custom_database_titles
from cmds.vector.call.call import (
    search as vt_search,
    search_custom_database_uuid as vt_search_custom_database_uuid,
    process_result as vt_process_result
)

logger = logging.getLogger(__name__)

# db = db_client['aichat_chat_history']
# 命名方式: 'ClassName_FunctionName_功能'
# db_key = 'aichat_chat_history'

async def xtts_available_lang_autocomplete(inter: discord.Interaction, current: str) -> list[Choice[str]]:
    langs = ["en","es","fr","de","it","pt","pl","tr","ru","nl","cs","ar","zh-cn","hu","ko","ja","hi"]
    
    if current:
        langs = [l for l in langs if l.lower().strip() in current.lower().strip()]

    return [Choice(name=l, value=l) for l in langs]

class AIChat(Cog_Extension):
    def __init__(self, bot):
        super().__init__(bot)
        self.db_client = mongo_db_client
        self.db = MongoDB_DB.aichat_chat_history

    async def cog_load(self):
        print(f'已載入「{__name__}」')

    @commands.Cog.listener()
    async def on_ready(self):
        await model.fetch_models()

    @commands.hybrid_command(name=locale_str('chat'), description=locale_str('chat'))
    @app_commands.describe(model=locale_str('chat_model'), is_vision_model = locale_str('chat_is_vision_model'))
    @app_commands.autocomplete(
        model = model_autocomplete,
        history = chat_history_autocomplete,
        system_prompt = system_prompt_autocomplete,
        vector_database_name = custom_database_titles
    )
    async def chat(
            self, 
            ctx: commands.Context, 
            prompt: str, 
            model: str = None, 
            history: str = None, 
            system_prompt: str = None,
            vector_database_name: str = None,
            enable_tools: bool = True, 
            image: Optional[discord.Attachment] = None, 
            text_file: Optional[discord.Attachment] = None,
            is_vision_model: bool = False
        ):
        try:
            await ctx.defer()

            db = self.db
            collection = db[str(ctx.author.id)]

            ls_history = None
            if history:
                result = await collection.find_one({
                    '_id': ObjectId(history)
                })
                if not result: return await ctx.send(f'Unknown error, cannot found any title called `{history}`')
                ls_history = result.get('messages')

            if system_prompt:
                system_prompt = await from_name_to_system_prompt(ctx.author.id, system_prompt)

            vector_database = None
            if vector_database_name:
                u = await vt_search_custom_database_uuid(ctx.author.id, vector_database_name)

                data = await vt_search(
                    prompt,
                    QdrantCollectionName.user_custom_database,
                    Filter(
                        must=[
                            FieldCondition(key='userID', match=MatchValue(value=ctx.author.id)),
                            FieldCondition(key='uuid', match=MatchValue(value=u))
                        ]
                    )
                )

                if data:
                    vector_database = vt_process_result(data)

            # keep last model
            if model:
                await redis_client.hset('last_model', str(ctx.author.id), model)
            else:
                model = (await redis_client.hget('last_model', str(ctx.author.id))) or 'cerebras:gpt-oss-120b'

            client = Chat(
                ctx=ctx,
                model=model,
                system_prompt=system_prompt
            )

            think, result, complete_history = await client.chat(
                prompt=prompt, 
                is_vision_model=is_vision_model, 
                history=ls_history, 
                is_enable_tools=enable_tools, 
                image=image, 
                text_file=text_file,
                vector_database=vector_database
            )

            '''i18n'''
            eb = load_translated(await ctx.interaction.translate('embed_chat'))[0]
            eb_title = eb.get('title')
            ''''''

            embed = create_basic_embed(title=eb_title, description=result, color=ctx.author.color)
            embed.set_footer(text=f"Powered by {model}{f' | database: {vector_database_name}' if vector_database_name else ''}")

            msg = await ctx.send(embed=embed)

            view = discord.ui.View()
            await add_history_button(msg, view, complete_history)
            await add_think_button(msg, view, think)

            if result:
                if history:
                    await collection.update_one({'_id': ObjectId(history)}, {'$set': {'messages': complete_history}}, upsert=True)
                else:
                    title = await gener_title(complete_history)
                    insert_result = await collection.insert_one({
                        'title': title,
                        'messages': complete_history,
                        'createAt': datetime.now().astimezone(timezone(timedelta(hours=8))).isoformat(), # +8
                    })
                    
                    # add to redis
                    async def add_to_redis(items: list[dict]):
                        await redis_client.zadd( # type: ignore
                            f'aichat_chat_history:{ctx.author.id}', 
                            { # type: ignore
                                orjson.dumps(item).decode(): datetime.fromisoformat(item.get('createAt', '1999-11-11T11:11:11+00:00')).timestamp()
                                for item in items
                                if item.get('createAt') and item.get('messages')
                            }
                        )
                        await redis_client.expire(f'aichat_chat_history:{ctx.author.id}', 60) # 1 分鐘過期
                    asyncio.create_task(add_to_redis(
                        [{
                                '_id': str(insert_result.inserted_id),
                                'title': title, 
                                'messages': complete_history, 
                                'createAt': datetime.now().astimezone(timezone(timedelta(hours=8))).isoformat()
                            }]
                        ))

            timeout = await view.wait()
            if timeout: await msg.edit(view=None)
        except openai.BadRequestError as e:
            logger.error('Error accured at chat command', exc_info=True)
            await ctx.send(f'Error accured :<\n{str(e)}', ephemeral=True)
        except:
            logger.error('Error accured at chat command', exc_info=True)
            await ctx.send('Error accured :<', ephemeral=True)

    @commands.hybrid_command(name=locale_str('del_chat_history'), description=locale_str('del_chat_history'))
    @app_commands.autocomplete(history = chat_history_autocomplete)
    @app_commands.describe(history = locale_str('del_chat_history_history'))
    async def del_chat_history(self, ctx: commands.Context, history: str):
        db = MongoDB_DB.aichat_chat_history
        collection = db[str(ctx.author.id)]

        result = await collection.find_one_and_delete({
            'title': history
        })
        if not result: return await ctx.send(f'Unknow error, cannot found any title called `{history}`', ephemeral=True)
        
        await ctx.send((await ctx.interaction.translate('send_del_chat_history_success')).format(history=history), ephemeral=True)

    @commands.hybrid_command(name=locale_str('image_generate'), description=locale_str('image_generate'))
    @app_commands.choices(
        img_generator_model=[
            Choice(name='cogview-3-flash', value='cogview-3-flash')
        ]
    )
    @app_commands.autocomplete(prompt_generator_model=model_autocomplete)
    async def _image_gener(self, ctx: commands.Context, prompt: str, img_generator_model: str = 'cogview-3-flash', prompt_generator_model: str = 'zhipu:glm-4-flash'):
        async with ctx.typing():
            try:
                visual_concept, url, time = await image_generate(prompt, img_generator_model, prompt_generator_model)

                '''i18n'''
                eb = load_translated(await ctx.interaction.translate('embed_image_generate'))[0]
                eb_title = eb.get('title')
                eb_field_1 = (eb.get('fields'))[0]
                field_name = eb_field_1.get('name')
                ''''''

                embed = create_basic_embed(title=eb_title, color=ctx.author.color)
                embed.set_image(url=url)
                embed.add_field(name='Visual Concept', value=visual_concept, inline=False)
                embed.add_field(name=field_name, value=int(time), inline=False)
                embed.set_footer(text=f'Powered by {prompt_generator_model} with {img_generator_model}')
                await ctx.send(embed=embed)
            except:
                logger.error('Error accured at image_generate command', exc_info=True)
                await ctx.send(await ctx.interaction.translate('send_image_generate_fail'), ephemeral=True)

    @commands.hybrid_command(name=locale_str('video_generate'), description=locale_str('video_generate'))
    @app_commands.choices(
        model=[Choice(name='cogvideox-flash', value='cogvideox-flash')],
        size = [
            Choice(name=size, value=size) 
            for size in ('720x480', '1024x1024', '1280x960', '960x1280', '1920x1080', '1080x1920', '2048x1080', '3840x2160')
        ],
        fps = [
            Choice(name=30, value=30),
            Choice(name=60, value=60)
        ]
    )
    @app_commands.describe(
        prompt=locale_str('video_generate_prompt'),
        image_url=locale_str('video_generate_image_url'),
        size=locale_str('video_generate_size'),
        fps=locale_str('video_generate_fps'),
        has_audio=locale_str('video_generate_has_audio'),
        duration=locale_str('video_generate_duration'),
        model=locale_str('video_generate_model')
    )
    async def _video_generate(
            self, ctx: commands.Context, *,
            prompt: str,
            image_url: str = None,
            size: str = None,
            fps: int = 60,
            has_audio: bool = True,
            duration: int = 5,
            model: str = 'cogvideox-flash'
        ):
        try:
            async with ctx.typing():
                if duration > 10:
                    await ctx.send(await ctx.interaction.translate('send_video_generate_duration_too_long').format(model=model), ephemeral=True)
                    duration = 10

                if fps not in (30, 60):
                    fps = 60

                try:
                    has_audio = bool(has_audio)
                except:
                    return await ctx.send(await ctx.interaction.translate('send_video_generate_wrong_type'))

                url, time = await video_generate(prompt, image_url, size, fps, has_audio, duration)
                string = (await ctx.interaction.translate('send_video_generate_success')).format(model=model, url=url, time=int(time))
                await ctx.send(string)
        except Exception as e:
            await ctx.send((await ctx.interaction.translate('send_video_generate_fail')).format(e=e), ephemeral=True)

    @commands.hybrid_command(name=locale_str('tts'), description=locale_str('tts'))
    @app_commands.choices(
        tts=[Choice(name=t, value=t) for t in ('xtts', 'f5tts')]
    )
    @app_commands.autocomplete(lang=xtts_available_lang_autocomplete)
    @app_commands.describe(sample_voice_file=locale_str('tts_sample_voice_file'), speed=locale_str('tts_speed'), lang=locale_str('tts_lang'))
    async def text_to_speech(self, ctx: commands.Context, text: str, sample_voice_file: Optional[discord.Attachment] = None, speed: float = 1.0, lang: str = 'zh-cn', tts: str = 'f5tts'):
        async with ctx.typing():
            if not 0 < speed <= 2.0: return await ctx.send(await ctx.interaction.translate('send_tts_speed_limit'))

            form = aiohttp.FormData()

            if sample_voice_file:
                file_bytes = await sample_voice_file.read()
                audio = MutagenFile(io.BytesIO(file_bytes))
                duration_sec = audio.info.length
                if duration_sec > 60: return await ctx.send(await ctx.interaction.translate('send_tts_duration_limit'))

                file_name = sample_voice_file.filename
                content_type = sample_voice_file.content_type or "application/octet-stream"

                form.add_field(
                    name="speaker_wav",
                    value=file_bytes,
                    filename=file_name,
                    content_type=content_type
                )

            form.add_field("text", text)
            form.add_field("speed", str(speed))
            if tts == 'xtts':
                form.add_field("lang", lang)
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(f'http://{OLLAMA_IP}:11198/generate/{tts}', data=form, timeout=60) as resp:
                        result = await resp.read()
            except aiohttp.ConnectionTimeoutError:
                return await ctx.send('Connection timeout, please try again later')

            bytes_io = io.BytesIO(result)
            file = discord.File(bytes_io, 'output.wav')
            await ctx.send(file=file)

async def setup(bot):
    await bot.add_cog(AIChat(bot))