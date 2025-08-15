from typing import AsyncGenerator
import logging

from crawl4ai.docker_client import Crawl4aiDockerClient  
from crawl4ai import BrowserConfig, CrawlerRunConfig  
from crawl4ai.content_filter_strategy import PruningContentFilter  
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator  
from crawl4ai.models import CrawlResult

from core.functions import DEVICE_IP

logger = logging.getLogger(__name__)

async def web_fetcher(url: str) -> str:
    try:
        final_result = []
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
            stream=True
        )  
        
        async with Crawl4aiDockerClient(base_url=f"http://{DEVICE_IP}:11235") as client:
            results: AsyncGenerator[CrawlResult] = await client.crawl(  
                [url],  
                browser_config=BrowserConfig(headless=True),  
                crawler_config=crawler_config  
            )  
            
            index = 1
            async for result in results:
                if result.success:
                    final_result.append(f'<web_search id={index} source_url: {result.url}>{result.markdown.fit_markdown}</web_search id={index}>')
                    index += 1
    except:
        logger.error('Error accred at web_search function: ', exc_info=True)
    finally:
        return '\n'.join(final_result) if final_result else "web_fetcher didn't find any answer."