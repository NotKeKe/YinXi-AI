from discord.ext import commands
from typing import Tuple
import asyncio
import orjson
import logging

from ..chat.chat import Chat
from ..utils.prompt import get_single_default_system_prompt
from ..tools.chat_human_tools.map import (
    map as chat_human_tool_map,
)

from core.mongodb_clients import MongoDB_DB
from core.functions import read_json, redis_client
from core.chat_human.prompt import get_current_system_prompt, get_current_user_prompt

model = 'lmstudio:unsloth/qwen3-8b'
logger = logging.getLogger(__name__)

async def get_example_response(user_prompt: str) -> str:
    # TODO
    ex_resp = ''
    return (
'''
## 回應範例
{ex_resp}
'''.format(ex_resp=ex_resp)
)

custom_tools_description: list = read_json('./cmds/ai_chat/tools/chat_human_tools/description.json')
with open('./cmds/ai_chat/data/prompts/chat_human_prompt_own_products.md', 'r', encoding='utf-8') as f:
    initial_system_prompt = f.read()

async def chat_human_chat(ctx: commands.Context, prompt: str, history: list, urls: list = None) -> Tuple[str, str]:
    client = Chat(
        model=model, 
        system_prompt=(await get_single_default_system_prompt(MongoDB_DB.system_prompt['default'], 'chat_human')) + (await get_example_response(prompt)), 
        ctx=ctx
    )

    think, result, complete_history = await client.chat(
        prompt, 
        history=history,
        url=urls,
        include_original_tools=True,
        custom_tool_description=custom_tools_description,
        custom_tools=chat_human_tool_map
    )

    return think, result

async def keep_think():
    collection = MongoDB_DB.self_growth_history['current_history']
    history = (await collection.find_one({'message': {'$exists': True}}) or {}).get('message') or []

    while True:
        try:
            client = Chat(
                model,
            )

            keke_send = await redis_client.get('keke_send_message')
            current_user_prompt = await get_current_user_prompt()
            prompt = current_user_prompt + (f'克克KeJC(管理員)進行了回覆: ```{keke_send}```' if keke_send else '')
            system_prompt = initial_system_prompt + (await get_current_system_prompt())

            think, result, history = await client.chat(
                prompt, 
                history=history,
                custom_system_prompt=initial_system_prompt + system_prompt,
                include_original_tools=True,
                custom_tool_description=custom_tools_description,
                custom_tools=chat_human_tool_map,
                tool_call_times=1
            )

            if current_user_prompt != 'system: 開始你的動作':
                await redis_client.delete('chat_human_current_user_prompt')

            if len(history) > 10:
                history = await client.summarize_history(history)

            await collection.update_one({'message': {'$exists': True}}, {'$set': {'message': history}}, upsert=True)
            await redis_client.delete('keke_send_message')
        except asyncio.CancelledError:
            logger.info('cancel keep_think')
        except:
            logger.error('Error accured at keep_think: ', exc_info=True)
        finally:
            await asyncio.sleep(10)