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

model = 'lmstudio:deepseek/deepseek-r1-0528-qwen3-8b'
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
        self.system_prompt_map = {
            'learning': 'self_growth_learning',
            'chatting': 'self_growth_chatting',
            'resting': 'self_growth_resting'
        }
        self.all_modes = list(self.mode_map.keys())

        self.pre_mode = None
        self.rest_time: int = 0

    async def run(self):
        await self.load_history()
        while True:
            try:
                # if self.mode == 'resting' and self.rest_time != 0:
                #     await asyncio.sleep(self.rest_time)
                #     self.rest_time = 0
                #     continue

                client = Chat(
                    model,
                )

                keke_send = await redis_client.get('keke_send_message')
                current_user_prompt = await get_current_user_prompt(self.mode)
                prompt = f"{f'克克KeJC(管理員)進行了回覆(請使用 call_keke 回覆你已經讀了這則訊息，並添加其他敘述(如果有需要)):\n  ```{keke_send}```' if keke_send else ''}\n{current_user_prompt}"
                system_prompt = f'已從 `{self.pre_mode}` 改為 `{self.mode}`' + (await get_single_default_system_prompt(self.system_prompt_map.get(self.mode, 'self_growth_learning'))) + (await get_current_system_prompt())

                await self.mode_map[self.mode](client, prompt, system_prompt)

                if current_user_prompt != f'#System: 請開始{self.mode}':
                    await redis_client.delete('chat_human_current_user_prompt')

                # if len(self.history) > 10:
                #     self.history = await client.summarize_history(self.history)

                await self.collection.update_one({'message': {'$exists': True}}, {'$set': {'message': self.history}}, upsert=True)
                if keke_send:
                    await redis_client.delete('keke_send_message')
            except asyncio.CancelledError:
                return logger.info('已取消 SelfGrowth')
            except:
                logger.error(f'Error accured at SelfGrowth, with {self.mode} mode: ', exc_info=True)
            finally:
                await asyncio.sleep(10)

    def switch_mode(self, mode: str):
        if mode not in self.all_modes: return f"切換失敗，目前僅支援以下模式: {str(self.all_modes)}，但是你使用了 `{mode}`"
        self.pre_mode = self.mode
        self.mode = mode

        string = f'已成功將現在的模式切換為 `{mode}`'
        logger.info(string)
        return string
    
    async def load_history(self):
        self.history = (await self.collection.find_one({'message': {'$exists': True}}) or {}).get('message') or []
    
    async def learning(self, client: Chat, user_prompt: str, system_prompt: str):
        think, result, self.history = await client.chat(
            user_prompt, 
            history=self.history,
            custom_system_prompt=system_prompt,
            include_original_tools=True,
            custom_tool_description=custom_tools_description,
            custom_tools=chat_human_tool_map,
            tool_call_times=1,
            temperature=1.2,
            repeat_penalty=1.3,
            frequency_penalty=0.8,
            presence_penalty=1.0,
            max_completion_tokens=2000
        )

    async def chatting(self, client: Chat, user_prompt: str, system_prompt: str):
        msgs = await redis_client.get('chat_human_sent_msgs')

        think, result, self.history = await client.chat(
            prompt=f"{f'以下為想跟你之前在{self.pre_mode}所忽略的訊息，請自行決定是否要回覆他們，你最多有10次機會可以回覆，其他未回覆的訊息將會被自動刪除。\n```json\n{msgs}\n```\n\n' if msgs else ''}\n{user_prompt}", 
            history=self.history,
            custom_system_prompt=system_prompt,
            include_original_tools=True,
            custom_tool_description=custom_tools_description,
            custom_tools=chat_human_tool_map,
            tool_call_times=10,
            repeat_penalty=1.3,
            max_completion_tokens=2000
        )

        await redis_client.delete('chat_human_sent_msgs')
    
    async def resting(self, client: Chat, user_prompt: str, system_prompt: str):
        think, result, self.history = await client.chat(
            user_prompt, 
            history=self.history,
            custom_system_prompt=system_prompt,
            include_original_tools=True,
            custom_tool_description=custom_tools_description,
            custom_tools=chat_human_tool_map,
            tool_call_times=1,
            repeat_penalty=1.3,
            max_completion_tokens=2000
        )

self_growth = SelfGrowth()