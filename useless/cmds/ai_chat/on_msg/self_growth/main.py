from discord.ext import commands
from typing import Tuple
import asyncio
import orjson
import logging
from typing import Literal, Optional
import random
from dataclasses import asdict
from datetime import datetime
from dacite import from_dict

from ...chat.chat import Chat
from ...utils.prompt import get_single_default_system_prompt
from ...tools.chat_human_tools.map import (
    map as chat_human_tool_map,
)
from .datacls import Status
from .datacls.types import *

from core.mongodb_clients import MongoDB_DB
from core.functions import read_json, redis_client, current_time
from core.chat_human.prompt import get_current_system_prompt, get_current_user_prompt

model = 'lmstudio:unsloth/qwen3-8b'
logger = logging.getLogger(__name__)

custom_tools_description: list = read_json('./cmds/ai_chat/tools/chat_human_tools/description.json') # type: ignore

class SelfGrowth:
    def __init__(self):
        self.collection = MongoDB_DB.self_growth_history['current_history']
        self.history = []
        self.status = Status()

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

        self.running: bool = False

    async def process_system_prompt(self) -> str:
        system_prompt = [
            (f'<mode_change>已從 `{self.status.pre_mode}` 改為 `{self.status.mode}`</mode_change>' if self.status.pre_mode != self.status.mode else ''), # mode change
            (await get_current_system_prompt() or ''), # llm custom system prompt
            ((await get_single_default_system_prompt(self.system_prompt_map.get(self.status.mode, 'self_growth_learning'))).format(time=current_time(), mood=self.status.mood.get_dominant_mood()) or '') # default system prompt
        ]
        return '\n'.join(system_prompt)
    
    async def process_user_prompt(self) -> str:
        keke_send = await redis_client.get('keke_send_message')
        current_user_prompt = await get_current_user_prompt(self.status.mode)

        prompt = [
            (f'克克KeJC(管理員)進行了回覆(請使用 call_keke 回覆你已經讀了這則訊息，並添加其他敘述(如果有需要)):\n  ```{keke_send}```' if keke_send else ''),
            current_user_prompt
        ]

        if current_user_prompt != f'#System: 你現在整處於{self.status.mode}，請使用適當工具進行{self.status.mode}':
            asyncio.create_task(redis_client.delete('chat_human_current_user_prompt')) # type: ignore

        return '\n'.join(prompt).strip()
    
    async def process_tool_called(self):
        '''
        處理工具調用所造成的情緒變化
        '''
        for h in self.history:
            _id = h.get('tool_call_id')
            if not _id: continue
            if (await redis_client.sismember('self_growth_called_tools', _id)): continue
            
            self.status.mood.called_tool(self.status.mode, h.get('content'))
                
        tool_called_ids = [_id for h in self.history for t in h.get('tool_calls', [{}]) if (_id := t.get('id'))]
        await redis_client.sadd('self_growth_called_tools', *tool_called_ids)

    async def run(self):
        await self.on_run()
        while True:
            try:
                client = Chat(
                    model,
                )

                if self.status.mood.tired <= 0.2:
                    self.status.mode = 'resting'
                
                system_prompt = await self.process_system_prompt()
                user_prompt = await self.process_user_prompt()
                await self.mode_map[self.status.mode](client, user_prompt, system_prompt) # call chat func

                await self.process_tool_called() # 工具調用的情緒變化
                await self.collection.update_one({'message': {'$exists': True}}, {'$set': {'message': self.history}}, upsert=True) # 聊天歷史紀錄
            except asyncio.CancelledError:
                await self.on_cancel()
                return logger.info('已取消 SelfGrowth')
            except:
                logger.error(f'Error accured at SelfGrowth, with {self.status.mode} mode: ', exc_info=True)
            finally:
                await asyncio.sleep(30)

    def switch_mode(self, mode: MODE_TYPE):
        if mode not in self.all_modes: return f"切換失敗，目前僅支援以下模式: {str(self.all_modes)}，但是你使用了 `{mode}`"
        self.status.pre_mode = self.status.mode
        self.status.mode = mode

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
            max_completion_tokens=5000
        )

    async def chatting(self, client: Chat, user_prompt: str, system_prompt: str):
        msgs = await redis_client.get('chat_human_sent_msgs')

        think, result, self.history = await client.chat(
            prompt=f"{f'以下為想跟你之前在{self.status.pre_mode}所忽略的訊息，請自行決定是否要回覆他們。\n```json\n{msgs}\n```\n\n' if msgs else ''}\n{user_prompt}", 
            history=self.history,
            custom_system_prompt=system_prompt,
            include_original_tools=True,
            custom_tool_description=custom_tools_description,
            custom_tools=chat_human_tool_map,
            tool_call_times=10,
            repeat_penalty=1.3,
            max_completion_tokens=5000
        )
    
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
            max_completion_tokens=5000
        )

    async def on_run(self):
        await self.load_history()
        await self._from_dict()
        self.running = True

    async def on_cancel(self):
        await self.save_to_dict()
        self.running = False


    async def _from_dict(self):
        collection = MongoDB_DB.self_growth_history['mood']
        data = await collection.find_one({'mood': {'$exists': True}})
        if not data: self.status = Status(); return
        self.status = from_dict(data_class=Status, data=data)

    async def save_to_dict(self):
        collection = MongoDB_DB.self_growth_history['mood']
        await collection.find_one_and_update({'mood': {'$exists': True}}, {'$set': {'savedAt': datetime.now().timestamp(), 'mood': asdict(self.status)}}, upsert=True)