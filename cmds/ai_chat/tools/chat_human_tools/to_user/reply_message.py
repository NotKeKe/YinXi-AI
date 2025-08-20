import asyncio
import discord
from typing import Any
import orjson

from core.classes import get_bot
from core.functions import redis_client

async def delete_replied_msg(data: dict[str, list[dict[str, Any]]], channel: discord.TextChannel, msg: discord.Message):
    def find():
        for item in data[str(channel.id)]:
            if item.get('msgID') == msg.id:
                data[str(channel.id)].remove(item)
                break
        return data
    data = await asyncio.to_thread(find)
    await redis_client.set('chat_human_sent_msgs', orjson.dumps(data, option=orjson.OPT_INDENT_2).decode())


async def reply_message(channelID: int, msgID: int, text: str):
    try:
        bot = get_bot()
        channel = bot.get_channel(int(channelID)) or await bot.fetch_channel(int(channelID))
        msg = await channel.fetch_message(msgID)
        await msg.reply(text)

        asyncio.create_task(delete_replied_msg(orjson.loads(await redis_client.get('chat_human_sent_msgs')), channel, msg))
        
        return '訊息傳送成功'
    except Exception as e:
        return f'Error: {str(e)}'