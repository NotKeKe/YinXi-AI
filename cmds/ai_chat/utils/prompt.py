from typing import List, Tuple
from motor.motor_asyncio import AsyncIOMotorCollection

from .config import mongo_db_client

KEY = 'system_prompt'

async def get_prompts(collection: AsyncIOMotorCollection) -> List[Tuple[str, str]]:
    '''
    Return name, prompt
    '''

    return [(item.get('name'), item.get('prompt')) async for item in collection.find() if item.get('name') and item.get('prompt')]

async def from_name_to_system_prompt(userID: int | str, name: str) -> str:
    collection = mongo_db_client[KEY][str(userID)]

    return (await collection.find_one({'name': name.strip()})).get('prompt')

async def upload_custom_system_prompt(userID: int | str, name: str, prompt: str):
    collection = mongo_db_client[KEY][str(userID)]

    await collection.insert_one({'name': name.strip(), 'prompt': prompt.strip()})

async def delete_custom_system_prompt(userID: int | str, name: str):
    collection = mongo_db_client[KEY][str(userID)]

    await collection.find_one_and_delete({'name': name.strip()})

async def in_custom_system_prompt(userID: int | str, name: str) -> bool:
    collection = mongo_db_client[KEY][str(userID)]

    return bool(await collection.find_one({'name': name.strip()}))