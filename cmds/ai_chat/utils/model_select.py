from openai import AsyncOpenAI
from typing import Union, Tuple
import logging
import re
import orjson

# from cmds.ai_three import availble_models

from .client import AsyncClient
from .config import db_client, redis_client

logger = logging.getLogger(__name__)


PROVIDERS = {
    'openrouter': AsyncClient.openrouter,
    'lmstudio': AsyncClient.lmstudio,
    'ollama': AsyncClient.ollama,
    'gemini': AsyncClient.gemini,
    'cerebras': AsyncClient.cerebras,
    'zhipu': AsyncClient.zhipu,
    'self_ollama': AsyncClient.self_ollama
}

def split_provider_model(provider_and_model: str) -> Tuple[str, str]:
    """Return provider, model

    Args:
        provider_and_model (str): _description_

    Returns:
        Tuple[str, str]: _description_
    """    
    match = re.match(r"(.*?)\s*:\s*(.*)", provider_and_model.strip())

    if match:
        provider = match.group(1)
        model = match.group(2)
        return provider, model
    
    return '', provider_and_model.strip()


async def model_select(original_model: str) -> Union[AsyncOpenAI, None]:
    provider, model = original_model.split(":", 1)

    logger.info(f'Got {provider=}, {model=}, {original_model=}')

    # db = db_client['aichat_available_models']
    # collection = db['models']

    # _id = 'model_setting'

    # result = await collection.find_one({'_id': _id})

    result = await redis_client.get('aichat_available_models')
    result = orjson.loads(result)

    for key in result:
        if provider and key.lower().strip() not in provider.lower().strip(): continue

        if model in set(result[key]):
            return PROVIDERS[key]
        
    return None