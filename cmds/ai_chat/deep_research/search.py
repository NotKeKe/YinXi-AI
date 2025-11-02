from typing import TYPE_CHECKING, Any
import aiohttp

from .utils import *

from core.functions import yinxi_base_url, DEVICE_IP

UA = f"YinXiAIBOT-DeepResearching ({yinxi_base_url})"

if TYPE_CHECKING:
    from .information import Info

class Search:
    def __init__(self, info: 'Info'):
        self.info = info

        self.session = aiohttp.ClientSession(headers={'User-Agent': UA}, connector=aiohttp.TCPConnector(limit=20, limit_per_host=5))

    async def first_search(self, keyword: str) -> list[tuple[str, str, str]]:
        '''
        透過 searxng，先取得大致的連結與 content，再由 llm 判斷是否保留
        Returns:
            [(url, title, content)]
        '''
        params = {
            'q': keyword,
            'format': 'json',
            'safesearch': 2,
        }
        async with self.session.get(f'http://{DEVICE_IP}:8080', params=params) as resp:
            data = await resp.json()

        data = data['results'][:20]

        results = [(item['url'], item['title'], item['content']) for item in data]

        return results
    
    async def ai_check_save(self, result: tuple[str, str, str]) -> Any:
        ...

    async def run(self, ):
        if not self.info.keywords: raise ValueError('keywords is empty')

        for question, keywords in self.info.keywords.items():
            for keyword in keywords:
                results = await self.first_search(keyword)
                # TODO