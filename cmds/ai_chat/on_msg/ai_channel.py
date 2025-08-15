from discord import Attachment
from discord.ext import commands
import asyncio
from typing import Tuple
import logging

from ..chat.chat import Chat
from ..utils.config import db_client, base_system_prompt

from core.mongodb_clients import MongoDB_DB

logger = logging.getLogger(__name__)

_id = 'ai_channel_setting'
db = MongoDB_DB.aichannel_chat_history

async def get_history(ctx: commands.Context) -> Tuple[list, bool]:
    collection = db[str(ctx.channel.id)]

    data = await collection.find_one({"messages": {"$exists": True}})
    meta_data = await db['CHANNELS'].find_one({'channel': ctx.channel.id})
    if data:
        return data.get('messages', []), meta_data.get('is_vision_model', False)

    return [], meta_data.get('is_vision_model', False)

async def save_history(ctx: commands.Context, history: list):
    try:
        collection = db[str(ctx.channel.id)]

        final_history = [h for h in history if not (h.get('tool_calls') or h.get('role') == 'tool' or h.get('tool_call_id'))]

        await collection.update_one(
        filter={"messages": {"$exists": True}},
        update={
            "$set": {
                "messages": final_history
            }
        }, 
        upsert=True)
    except:
        logger.error('Error accured at save_history', exc_info=True)


async def ai_channel_chat(ctx: commands.Context, prompt: str, model: str, system_prompt: str = None, urls: list = None, image: Attachment = None) -> Tuple[str, str, list]:
    system_prompt = system_prompt or base_system_prompt
    client = Chat(model, system_prompt, ctx)

    history, vision = await get_history(ctx)

    think, result, complete_history = await client.chat(
        f'`{(ctx.author.global_name)}` said: 「{prompt}」', 
        history=history,
        url=urls,
        image=image,
        is_vision_model=vision
    )

    asyncio.create_task(save_history(ctx, complete_history))

    return think, result, complete_history