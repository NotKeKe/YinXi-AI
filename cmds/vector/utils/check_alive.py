import aiohttp
from .client import AsyncClient

connector = aiohttp.TCPConnector()
connected = False

async def connection_check() -> bool:
    '''
    Check if OLLAMA_IP exists, if not return False
    '''
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get('http:ollama:11434') as resp:
            if resp.status == 200:
                global connected
                connected = True