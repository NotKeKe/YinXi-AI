import aiohttp

from .client import AsyncClient
from .config import redis_client
from core.functions import OLLAMA_IP

async def connection_check() -> bool:
    '''
    Check if lmstudio healthy, if not return False
    '''
    async with aiohttp.ClientSession() as session:
        async with session.get(f'http://{OLLAMA_IP}:1239') as resp:
            await redis_client.set('lmstudio_is_connected', 1 if resp.status == 200 else 0)

async def get_connection_status() -> bool:
    result = await redis_client.get('lmstudio_is_connected')
    return result == '1'