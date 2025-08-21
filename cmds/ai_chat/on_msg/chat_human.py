from discord.ext import commands
from typing import Tuple
import asyncio
import orjson
import logging
from typing import Literal

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
# with open('./cmds/ai_chat/data/prompts/chat_human_prompt_own_products.md', 'r', encoding='utf-8') as f:
#     initial_system_prompt = f.read()

async def chat_human_chat(ctx: commands.Context, prompt: str, history: list, urls: list = None) -> Tuple[str, str]:
    client = Chat(
        model=model, 
        system_prompt=(await get_single_default_system_prompt('chat_human')) + (await get_example_response(prompt)), 
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

