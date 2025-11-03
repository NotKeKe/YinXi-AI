from typing import TYPE_CHECKING
import aiohttp
from bs4 import BeautifulSoup
from collections import defaultdict

from .utils import *

from core.functions import yinxi_base_url, DEVICE_IP, split_str_by_len_and_backtick

UA = f"YinXiAIBOT-DeepResearching ({yinxi_base_url})"

if TYPE_CHECKING:
    from .information import Info

SYSTEM_PROMPT = '''
你是一個研究助手，請從使用者提供的資訊執行以下任務:
1. 根據使用者的問題，查看每個連結的內文，是否能夠提供與問題相關的答案。
2. 判斷每個連結是否具有可信度，並決定是否保留。
3. 在不使用任何 markdown 格式的情況下，依據輸出格式做輸出。

輸出格式:
['URL 1', 'URL 2'...]
'''

class Search:
    def __init__(self, info: 'Info'):
        self.info = info

        self.session = aiohttp.ClientSession(headers={'User-Agent': UA}, connector=aiohttp.TCPConnector(limit=20, limit_per_host=5))

    async def first_search(self, keyword: str) -> list[tuple[str, str, str]]:
        '''
        透過 searxng，先取得大致的連結與 content
        Returns:
            [(url, title, content)]
        '''
        params = {
            'q': keyword,
            'format': 'json',
            'safesearch': 2,
        }
        try:
            async with self.session.get(f'http://{DEVICE_IP}:8080', params=params) as resp:
                resp.raise_for_status()
                data = await resp.json()
        except:
            raise Exception('Searxng error in Deep Reasearch')

        data = data['results'][:20]

        results = [(item['url'], item['title'], item['content']) for item in data]

        return results
    
    async def fetch_website(self, url: str) -> str: # return content
        try:
            async with self.session.get(url) as resp:
                resp.raise_for_status()
                text = await resp.text()

            soup = BeautifulSoup(text, "html.parser")

            title = soup.title.string.strip() if soup.title else ''

            paragraphs = [str(p.text).strip() for p in soup.find_all("p")]
            content = "\n".join(paragraphs)

            final_result = f'Title: "{title}"\nContent:\n```\n{content}\n```'

            return final_result
        except Exception as e:
            print('Deep research error, url:', url, e) # TODO: maybe ignore failed url
            return ''

    async def run(self, ):
        if not self.info.keywords: raise ValueError('keywords is empty')

        final_result: dict[str, list[tuple[(str, str)]]] = {} # question: [(url, content)]

        for question, keywords in self.info.keywords.items():
            fetch_results: list[tuple[str, str]] = []

            # 取得所有關鍵字-url
            for keyword in keywords:
                results = await self.first_search(keyword) # 取得全部連結
                urls = [item[0] for item in results]

                # 取得每個 url 的內文
                for url in urls:
                    website_result = await self.fetch_website(url)
                    if not (website_result and url): continue
                    fetch_results.append((url, website_result))

            final_result[question] = fetch_results 

        # add to chromadb
        all_data: dict[str, list] = defaultdict(list)
        '''
        {
            documents: [
                'content1', 
                'content2'
            ],
            'metas: [
                {'sub_question': 'sub_question1', 'url': 'url1'},
                {'sub_question': 'sub_question2', 'url': 'url2'}
            ]
        }
        '''
        for question, results in final_result.items():
            for url, content in results:
                contents = split_str_by_len_and_backtick(content, 1000) # 避免長度過長
                for c in contents:
                    all_data['documents'].append(c)
                    all_data['metas'].append({'sub_question': question, 'url': url})

        await TempVector.add(self.info.uuid, all_data['documents'], all_data['metas'])
            
    async def _task_run(self): # same as run, but in asyncio.Task s
        if not self.info.keywords: raise ValueError('keywords is empty')

        final_result: dict[str, list[tuple[(str, str)]]] = {} # question: [(url, content)]

        for question, keywords in self.info.keywords.items():
            fetch_results: list[tuple[str, str]] = []

            # 取得所有關鍵字-url
            first_searches = [self.first_search(keyword) for keyword in keywords]
            first_search_results = await asyncio.gather(*first_searches)
            urls = [item[0] for results in first_search_results for item in results]

            # 取得所有連結內文
            website_results = [self.fetch_website(url) for url in urls]
            website_results = await asyncio.gather(*website_results)

            # 取得最終結果 (url, content)
            fetch_results = [(url, content) for url, content in zip(urls, website_results) if content and url]

            final_result[question] = fetch_results 

        # add to chromadb
        all_data: dict[str, list] = defaultdict(list)
        '''
        {
            documents: [
                'content1', 
                'content2'
            ],
            'metas: [
                {'sub_question': 'sub_question1', 'url': 'url1'},
                {'sub_question': 'sub_question2', 'url': 'url2'}
            ]
        }
        '''
        for question, results in final_result.items():
            for url, content in results:
                contents = split_str_by_len_and_backtick(content, 1000) # 避免長度過長
                for c in contents:
                    all_data['documents'].append(c)
                    all_data['metas'].append({'sub_question': question, 'url': url})

        await TempVector.add(self.info.uuid, all_data['documents'], all_data['metas'])