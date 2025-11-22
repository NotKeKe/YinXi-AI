from discord import app_commands, Interaction
from discord.app_commands import Choice
from typing import List
import orjson
from datetime import datetime
import asyncio

from core.functions import UnixToReadable, redis_client
from core.mongodb_clients import MongoDB_DB
from .config import db_client, redis_client, high_model_providers, high_model_users
from .prompt import (
    get_prompts,
    KEY as SYSTEM_PROMPT_KEY
)

async def chat_history_autocomplete(interaction: Interaction, current: str) -> List[Choice[str]]:
    # 1999-11-11T11:11:11+00:00 只是用於排除例外情況
    db = MongoDB_DB.aichat_chat_history
    collection = db[str(interaction.user.id)]

    data: list[tuple[str, datetime, str]] = []

    _temp_data = await redis_client.zrevrange(f'aichat_chat_history:{interaction.user.id}', 0, 25) # 從後往前
    temp_data = []
    if _temp_data:
        for val in _temp_data:
            item = orjson.loads(val)
            title = item.get('title') or 'Unknown conversation'
            time = item.get('createAt', '')
            _id = str(item.get('_id', ''))
            if not _id: print('No _id') ; continue

            time = datetime.fromisoformat(time)
            temp_data.append((title, time, _id))

    # 先從 redis 拿資料，加快速度
    if temp_data:
        data = temp_data
    else:
        to_add_items: list[dict] = [] # 用於事後從 mongodb 加進 redis
        # find from mongodb
        async for d in collection.find():
            title = d.get('title') or 'Unknown conversation'
            time = d.get('createAt', '1999-11-11T11:11:11+00:00')
            _id = str(d.get('_id', ''))
            if not _id: print('No _id') ; continue

            time = datetime.fromisoformat(time)

            to_add_items.append(d | {'_id': _id})
            data.append((title, time, _id))
        
        # add to redis
        async def add_to_redis(items: list[dict]):
            await redis_client.zadd( # type: ignore
                f'aichat_chat_history:{interaction.user.id}', 
                { # type: ignore
                    orjson.dumps(item).decode(): datetime.fromisoformat(item.get('createAt', '1999-11-11T11:11:11+00:00')).timestamp()
                    for item in items
                    if item.get('createAt') and item.get('messages')
                }
            )
            await redis_client.expire(f'aichat_chat_history:{interaction.user.id}', 120) # 2 分鐘過期
        asyncio.create_task(add_to_redis(to_add_items))
        
    if current:
        data = [(title, time, _id) for title, time, _id in data if title and current.lower().strip() in title.lower().strip()]

    data.sort(key=lambda x: x[1], reverse=True)

    # 限制最多回傳 25 個結果
    return [Choice(name=f'{title} ({time.strftime("%Y-%m-%d %H:%M:%S %Z")})'[:100], value=_id) for title, time, _id in data[:25] if title]

async def model_autocomplete(interaction: Interaction, current: str) -> List[Choice[str]]:
    result = await redis_client.get('aichat_available_models')
    result = orjson.loads(result)

    models = []
    for provider, item in dict(result).items():
        if provider == '_id': continue
        if provider in high_model_providers:
            if interaction.user.id not in high_model_users: continue
        
        for model in item:
            models.append((provider, model))

    if current:
        models = [(provider, m) for provider, m in models if current.lower().strip() in m.lower().strip() or current.lower().strip() in provider.lower().strip()]
        models.sort(key=lambda x: x[1])
    
    return [Choice(name=f"[{provider}] {model}", value=f"{provider}:{model}") for provider, model in models[:25]]

def process_three_dot(name: str, prompt: str) -> str:
    size = len(name + prompt)

    if size <= 100:
        return f'[{name}] {prompt}'
    else: # 最大長度 - ... - `[] ` - len(name)
        return f'[{name}] {prompt[:(100-3-(3+len(name)))]}...'

async def default_system_prompt(inter: Interaction, current: str) -> List[Choice[str]]:
    collection = db_client[SYSTEM_PROMPT_KEY]['default']
    prompts = await get_prompts(collection)

    if current:
        prompts = [
            item
            for item in prompts 
            if current.lower().strip() in item[0].lower().strip()
            or
            current.lower().strip() in item[1].lower().strip()
        ]

    return [Choice(name=process_three_dot(item[0], item[1]), value=item[0]) for item in prompts[:25]]

async def custom_user_system_prompt_for_del(inter: Interaction, curr: str) -> List[Choice[str]]:
    db = db_client[SYSTEM_PROMPT_KEY]
    collection = db[str(inter.user.id)]

    data = await get_prompts(collection)

    if curr:
        data = [ 
            item
            for item in data 
            if curr.lower().strip() in item[0].lower().strip()
            or
            curr.lower().strip() in item[1].lower().strip()
        ] 

    return [Choice(name=process_three_dot(item[0], item[1]), value=item[0]) for item in data[:25]]

async def system_prompt_autocomplete(inter: Interaction, curr: str) -> List[Choice[str]]:
    db = db_client[SYSTEM_PROMPT_KEY]
    collection = db[str(inter.user.id)]
    data = await get_prompts(collection)

    collection = db['default']
    data += await get_prompts(collection)

    if curr:
        data = [ 
            item
            for item in data 
            if curr.lower().strip() in item[0].lower().strip()
            or
            curr.lower().strip() in item[1].lower().strip()
        ] 

    return [Choice(name=process_three_dot(item[0], item[1]), value=item[0]) for item in data[:25]]