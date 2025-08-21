from aiohttp import ClientSession
from typing import AsyncGenerator
import logging

from crawl4ai.docker_client import Crawl4aiDockerClient  
from crawl4ai import BrowserConfig, CrawlerRunConfig  
from crawl4ai.content_filter_strategy import PruningContentFilter  
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator  
from crawl4ai.models import CrawlResult

from core.functions import DEVICE_IP

NOT_AVAILABLE = 'web_search is not available'
logger = logging.getLogger(__name__)

async def web_search(keywords: str, time_range: str = 'year', language: str = 'zh-TW') -> str:
    final_result = []
    try:
        time_range = ('day' if time_range.lower().strip() not in ('year', 'month', 'week', 'day') else time_range.lower().strip()) if time_range else None

        params = {
            'q': keywords,
            'format': 'json',
            'safesearch': 2,
            'language': language,
            **({'time_range': time_range} if time_range is not None and time_range != '' else {}),
        }

        async with ClientSession() as session:
            async with session.get(f'http://{DEVICE_IP}:8080', params=params) as resp:
                if resp.status != 200:
                    return NOT_AVAILABLE
                
                try:
                    data = await resp.json()
                except Exception as e:
                    print(f'Error while calling web_search: {e}')
                    return NOT_AVAILABLE
                    
                
        urls = [item['url'] for item in data['results']][:10]

        md_generator = DefaultMarkdownGenerator(  
            content_filter=PruningContentFilter(threshold=0.6),  
            options={  
                "ignore_links": True,  
                "ignore_images": True,  
                "body_width": 0  
            }  
        )  
        
        crawler_config = CrawlerRunConfig(  
            markdown_generator=md_generator,  
            exclude_external_links=True,  
            word_count_threshold=10,
            stream=True,
            wait_for_timeout=5
        )  
        
        async with Crawl4aiDockerClient(base_url=f"http://{DEVICE_IP}:11235") as client:
            results: AsyncGenerator[CrawlResult] = await client.crawl(  
                urls,  
                browser_config=BrowserConfig(headless=True),  
                crawler_config=crawler_config  
            )  
            
            index = 1
            try:
                async for result in results:
                    if result.success:
                        final_result.append(f'<web_search id={index} source_url: {result.url}>{result.markdown.fit_markdown[:1000]}</web_search id={index}>')
                        index += 1
            except Exception as e:
                logger.error(f"Error accured at web_search funciotn's async for: {str(e)}")
    except Exception as e:
        logger.error('Error accured at web_search function: ', exc_info=True)
        return f'web_search returned a error: {e}'

    if not final_result: return "web_search didn't find any answer."

    return '\n'.join(final_result)

async def not_available_web_search(keywords: str, time_range: str = 'year', language: str = 'zh-TW') -> str:
    # 先查資料庫中有沒有對應的資料 再進行搜尋
    # sql_data = knowledge_base_search(keywords)
    # result = [sql_data] if sql_data else []
    result = []
    time_range = ('day' if time_range.lower().strip() not in ('year', 'monuth', 'week', 'day') else time_range.lower().strip()) if time_range else None

    url = f'http://{DEVICE_IP}:8080'
    params = {
        'q': keywords,
        'format': 'json',
        'safesearch': 2,
        'language': language,
        **({'time_range': time_range} if time_range is not None and time_range != '' else {}),
    }

    async with ClientSession() as session:
        async with session.get(f'http://{DEVICE_IP}:8080', params=params) as resp:
            if resp.status != 200:
                return NOT_AVAILABLE
            
            try:
                data = await resp.json()
            except Exception as e:
                print(f'Error while calling web_search: {e}')
                return NOT_AVAILABLE
                
            
    urls = [item['url'] for item in data['results']][:10]

    async def scrape_page(url: str) -> str:
        # headers = {"User-Agent": 'Mozilla/5.0'}

        # async with ClientSession() as session:
        #     async with session.get(url, headers=headers, timeout=5) as resp:
        #         if resp.status != 200: return 'None', 'None'
        #         text = await resp.text()

        # soup = BeautifulSoup(text, "html.parser")
        # titleObj = soup.find("title")

        # if titleObj is None: return None, None

        # title = titleObj.text
        # paragraphs = [p.text for p in soup.find_all("p")]
        # content = "\n".join(paragraphs)

        # return title, content
        
         
        # 配置輕量級的 markdown 生成器  
        ...
    
    for url in urls:
        try:
            if url.endswith('.pdf'): continue
            title, content = await scrape_page(url)
            if title is None and content is None: continue
            result.append(f"標題: {title}\n內容: {content[:400]}...\n連結: {url}\n")  # 只顯示前200字
        except Exception as e:
            print(f"爬取失敗: {url}, 錯誤: {e}")

    if not result: return "web_search didn't find any answer."

    return '\n'.join(result)