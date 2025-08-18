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

model = 'lmstudio:qwen/qwen3-4b'
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

class SelfGrowth:
    def __init__(self):
        self.mode: Literal['learning', 'chatting', 'resting'] = 'learning'

        self.collection = MongoDB_DB.self_growth_history['current_history']
        self.history = []

        self.mode_map = {
            'learning': self.learning,
            'chatting': self.chatting,
            'resting': self.resting
        }
        self.all_modes = list(self.mode_map.keys())

    async def run(self):
        while True:
            try:
                await self.mode_map[self.mode]()
            except asyncio.CancelledError:
                return logger.info('已取消 SelfGrowth')
            except:
                logger.error(f'Error accured at SelfGrowth, with {self.mode} mode: ', exc_info=True)
            finally:
                await asyncio.sleep(10)

    def switch_mode(self, mode: str):
        if mode not in self.all_modes: return f"切換失敗，目前僅支援以下模式: {str(self.all_modes)}，但是你使用了 `{mode}`"
        self.mode = mode
        return f'已成功將現在的模式切換為 `{mode}`'
    
    async def load_history(self):
        self.history = (await self.collection.find_one({'message': {'$exists': True}}) or {}).get('message') or []
    
    async def learning(self):
        await self.load_history()

        client = Chat(
            model,
        )

        keke_send = await redis_client.get('keke_send_message')
        current_user_prompt = await get_current_user_prompt()
        prompt = current_user_prompt + '\n' + (f'克克KeJC(管理員)進行了回覆:\n  ```{keke_send}```' if keke_send else '')
        system_prompt = initial_system_prompt + (await get_current_system_prompt())

        think, result, self.history = await client.chat(
            prompt, 
            history=self.history,
            custom_system_prompt=initial_system_prompt + system_prompt,
            include_original_tools=True,
            custom_tool_description=custom_tools_description,
            custom_tools=chat_human_tool_map,
            tool_call_times=1
        )

        if current_user_prompt != 'system: 開始你的動作':
            await redis_client.delete('chat_human_current_user_prompt')

        if len(self.history) > 10:
            self.history = await client.summarize_history(self.history)

        await self.collection.update_one({'message': {'$exists': True}}, {'$set': {'message': self.history}}, upsert=True)
        await redis_client.delete('keke_send_message')

    async def chatting(self):
        pass
    
    async def resting(self):
        pass

self_growth = SelfGrowth()