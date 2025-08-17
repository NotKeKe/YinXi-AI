from discord.ext import commands
import asyncio
from typing import Tuple

from ..chat.chat import Chat
from ..utils.prompt import get_single_default_system_prompt

from core.mongodb_clients import MongoDB_DB

model = 'lmstudio:qwen3-8b'

async def get_example_response(user_prompt: str) -> str:
    # TODO
    ex_resp = ''
    return (
'''
## 回應範例
{ex_resp}
'''.format(ex_resp=ex_resp)
)

async def chat_human_chat(ctx: commands.Context, prompt: str, history: list, urls: list = None) -> Tuple[str, str]:
    client = Chat(
        model=model, 
        system_prompt=(await get_single_default_system_prompt(MongoDB_DB.system_prompt['default'], 'chat_human')) + (await get_example_response(prompt)), 
        ctx=ctx
    )

    think, result, complete_history = await client.chat(
        prompt, 
        history=history,
        url=urls
    )

    return think, result