from discord import app_commands, Interaction
from discord.app_commands import Choice
from typing import List

from core.functions import UnixToReadable
from .config import db_client
from .prompt import get_prompts

async def chat_history_autocomplete(interaction: Interaction, current: str) -> List[Choice[str]]:
    db = db_client['aichat_chat_history']
    collection = db[str(interaction.user.id)]
    
    data = [
        (d.get('title', ''), d.get('createAt', 0)) 
        async for d in collection.find() 
    ]
        
    if current:
        data = [(title, time) for title, time in data if current.lower().strip() in title.lower().strip() and title != '']

    data.sort(key=lambda x: x[1], reverse=True)

    # 限制最多回傳 25 個結果
    return [Choice(name=f'{title} ({UnixToReadable(time)})', value=title) for title, time in data[:25] if title != '']

async def model_autocomplete(interaction: Interaction, current: str) -> List[Choice[str]]:
    db = db_client['aichat_available_models']
    collection = db['models']

    _id = 'model_setting'

    result = await collection.find_one({'_id': _id})

    models = [(provider, model) for provider, item in dict(result).items() if provider != '_id' for model in item]

    if current:
        models = [(provider, m) for provider, m in models if current.lower().strip() in m.lower().strip() or current.lower().strip() in provider.lower().strip()]
        models.sort(key=lambda x: x[1])
    
    return [Choice(name=f"[{provider}] {model}", value=f"{provider}:{model}") for provider, model in models[:25]]

async def default_system_prompt(inter: Interaction, current: str) -> List[Choice[str]]:
    prompts = await get_prompts()

    if current:
        prompts = [
            item
            for item in prompts 
            if current.lower().strip() in item[0].lower().strip()
            or
            current.lower().strip() in item[1].lower().strip()
        ]

    return [Choice(name=f'[{item[0]}] {item[1][:10]}...', value=item[1]) for item in prompts[:25]]

async def custom_user_system_prompt_for_del(inter: Interaction, curr: str) -> List[Choice[str]]:
    db = db_client['system_prompt']
    collection = db[str(inter.user.id)]

    data = [(item.get('name'), item.get('prompt')) async for item in collection.find() if item.get('name') and item.get('prompt')]

    if curr:
        data = [ 
            item
            for item in data 
            if curr.lower().strip() in item[0].lower().strip()
            or
            curr.lower().strip() in item[1].lower().strip()
        ] 

    return [Choice(name=f'[{item[0]}] {item[1][:10]}...', value=item[0]) for item in data[:25]]

async def custom_user_system_prompt_for_use(inter: Interaction, curr: str) -> List[Choice[str]]:
    db = db_client['system_prompt']
    collection = db[str(inter.user.id)]

    data = [(item.get('name'), item.get('prompt')) async for item in collection.find() if item.get('name') and item.get('prompt')]

    if curr:
        data = [ 
            item
            for item in data 
            if curr.lower().strip() in item[0].lower().strip()
            or
            curr.lower().strip() in item[1].lower().strip()
        ] 

    return [Choice(name=f'[{item[0]}] {item[1][:10]}...', value=item[1]) for item in data[:25]]