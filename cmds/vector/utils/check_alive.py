import aiohttp
from .client import AsyncClient

connected = False

async def connection_check(session: aiohttp.ClientSession) -> bool:
    '''
    Check if OLLAMA_IP exists, if not return False
    '''
    async with session.get('http://ollama:11434') as resp:
        if resp.status == 200:
            global connected
            connected = True

    return connected