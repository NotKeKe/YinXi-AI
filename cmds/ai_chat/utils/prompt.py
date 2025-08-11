from typing import List, Tuple
from motor.motor_asyncio import AsyncIOMotorCollection

from .config import mongo_db_client

KEY = 'system_prompt'

class DefaultSystemPrompts:
    class Base:
        base_yinxi = ''
        chat_huamn = ''

    class CosPlay:
        ...

    class Question:
        socratic_method = '我希望你扮演蘇格拉底。你必須使用蘇格拉底詰問法來不斷質疑我的信念。我會發表一個聲明，你將嘗試進一步質疑每個聲明，以測試我的邏輯。你每次只能回應一行。'

    class Creative:
        story_teller = ''
        mystery_novel = ''
        image_generate = ''

    class Utils:
        summary = ''

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