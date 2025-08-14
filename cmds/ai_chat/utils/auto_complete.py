from discord import app_commands, Interaction
from discord.app_commands import Choice
from typing import List
import orjson

from core.functions import UnixToReadable
from .config import db_client, redis_client
from .prompt import (
    get_prompts,
    KEY as SYSTEM_PROMPT_KEY
)

async def chat_history_autocomplete(interaction: Interaction, current: str) -> List[Choice[str]]:
    db = db_client['aichat_chat_history']
    collection = db[str(interaction.user.id)]
    
    data = [
        (d.get('title', ''), d.get('createAt', 0)) 
        async for d in collection.find() 
    ]
        
    if current:
        data = [(title, time) for title, time in data if title and current.lower().strip() in title.lower().strip()]

    data.sort(key=lambda x: x[1], reverse=True)

    # 限制最多回傳 25 個結果
    return [Choice(name=f'{title} ({UnixToReadable(time)})', value=title) for title, time in data[:25] if title]

async def model_autocomplete(interaction: Interaction, current: str) -> List[Choice[str]]:
    result = await redis_client.get('aichat_available_models')
    result = orjson.loads(result)

    models = [(provider, model) for provider, item in dict(result).items() if provider != '_id' for model in item]

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