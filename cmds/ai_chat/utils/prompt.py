from typing import List, Tuple
from motor.motor_asyncio import AsyncIOMotorCollection

from .config import mongo_db_client

from cmds.ai_chat.utils.config import base_system_prompt
from core.functions import redis_client
from core.mongodb_clients import MongoDB_DB

KEY = 'system_prompt'
REDIS_default_system_prompts_KEY = 'default_system_prompts:'

async def get_prompts(collection: AsyncIOMotorCollection) -> List[Tuple[str, str]]:
    '''
    Return name, prompt
    '''
    return [(item.get('name'), item.get('prompt')) async for item in collection.find() if item.get('name') and item.get('prompt')]

async def get_single_default_system_prompt(collection: AsyncIOMotorCollection, name: str) -> str:
    prompt = await redis_client.hget(REDIS_default_system_prompts_KEY, name)
    if not prompt:
        collection = MongoDB_DB.system_prompt['default']
        data = await collection.find_one({'name': name})
        prompt = data.get('prompt', '')

        # 寫進 Redis
        if prompt:
            await redis_client.hset(REDIS_default_system_prompts_KEY, name, prompt)
            await redis_client.expire(REDIS_default_system_prompts_KEY, 60 * 10) # 10 mins
    return prompt

async def from_name_to_system_prompt(userID: int | str, name: str) -> str:
    collection = mongo_db_client[KEY][str(userID)]

    data = await collection.find_one({'name': name.strip()})

    return data.get('prompt') if data else base_system_prompt

async def upload_custom_system_prompt(userID: int | str, name: str, prompt: str):
    collection = mongo_db_client[KEY][str(userID)]

    await collection.insert_one({'name': name.strip(), 'prompt': prompt.strip()})

async def delete_custom_system_prompt(userID: int | str, name: str):
    collection = mongo_db_client[KEY][str(userID)]

    await collection.find_one_and_delete({'name': name.strip()})

async def in_custom_system_prompt(userID: int | str, name: str) -> bool:
    collection = mongo_db_client[KEY][str(userID)]

    return bool(await collection.find_one({'name': name.strip()}))