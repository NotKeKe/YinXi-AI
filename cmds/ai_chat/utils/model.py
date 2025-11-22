import logging
import orjson
from openai import AsyncOpenAI
import asyncio
from typing import Callable

from .client import AsyncClient
from .config import db_client, redis_client

logger = logging.getLogger(__name__)

async def fetch(client: AsyncOpenAI, condition: Callable[..., bool] = lambda x: True, name: str = 'Unknown') -> tuple[list, str]:
    try:
        return [
            model.id 
            for model in (await client.models.list()).data
            if condition(model)
        ], name
    except Exception as e:
        logger.error(f"Cannot fetch {name}'s models: {e}")
        return [], name

async def fetch_models():
    tasks = [
        fetch(AsyncClient.openrouter, lambda x: x.id.endswith('free') or x.id == 'openrouter/horizon-beta', 'openrouter'),
        fetch(AsyncClient.ollama, name='ollama'),
        fetch(AsyncClient.cerebras, name='cerebras'),
        fetch(AsyncClient.lmstudio, name='lmstudio'),
        fetch(AsyncClient.self_ollama, name='self_ollama'),
    ]

    zhipu_models = [
        'glm-4-flash',
        'glm-4.5-flash',
        'glm-z1-flash',
        'glm-4-flash-250414'
    ]
    gemini_models = [
        'gemini-2.5-pro',
        'gemini-2.5-flash',
        'gemma-3-27b-it',
    ]
    doubao_models = [
        'doubao'
    ]

    results = await asyncio.gather(*tasks)

    data = {
        'openrouter': [item[0] for item in results if item[1] == 'openrouter'][0],
        'zhipu': zhipu_models,
        'ollama': [item[0] for item in results if item[1] == 'ollama'][0],
        'gemini': gemini_models,
        'cerebras': [item[0] for item in results if item[1] == 'cerebras'][0],
        'lmstudio': [item[0] for item in results if item[1] == 'lmstudio'][0],
        'self_ollama': [item[0] for item in results if item[1] == 'self_ollama'][0],
        'doubao': doubao_models
    }

    await redis_client.unlink('aichat_available_models')
    await redis_client.sadd('aichat_available_models', *[f'{provider}:{model}' for provider, models in data.items() for model in models]) # type: ignore