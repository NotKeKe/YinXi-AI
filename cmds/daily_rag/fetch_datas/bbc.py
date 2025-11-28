from httpx import AsyncClient
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from newspaper import Article
from datetime import timezone, timedelta
import asyncio
import logging
import orjson
import logging

from .config import JSONL_PATH

logger = logging.getLogger(__name__)

BASE_URL = 'https://www.bbc.com'

def get_article_data(url: str) -> dict:
    try:
        article = Article(url)
        article.download()
        article.parse()

        title = article.title
        text = article.text_cleaned.strip()
        publish_time = article.publish_date
        if publish_time:
            publish_time = publish_time.astimezone(timezone(timedelta(hours=8))).isoformat()

        return {'title': title, 'text': text, 'url': url, 'publish_time': publish_time}
    except:
        logger.error(f'Error occurred while fetching article {url} in bbc', exc_info=True)
        return {}
    
def process_and_save_dataset(urls: set[str]):
    with open(JSONL_PATH, 'ab', buffering=1024*1024*4) as f:
        for url in urls:
            raw_data = get_article_data(url)
            if not raw_data: continue

            title = raw_data['title']
            text = raw_data['text']
            url = raw_data['url']
            publish_time = raw_data['publish_time']

            f.write(orjson.dumps({'text': text, 'meta': {'title': title, 'url': url, 'time': publish_time}}) + b'\n')


async def fetch_bbc(client: AsyncClient):
    logger.info('Fetching BBC')
    resp = await client.get(urljoin(BASE_URL, '/news'))

    soup = BeautifulSoup(resp.text, 'html.parser')

    # get all today's article urls
    urls = set()
    for link in soup.find_all('a'):
        href = link.get('href')
        if not href.startswith('http'):
            href = urljoin(BASE_URL, href)

        parsed_url = urlparse(href)

        if not parsed_url.netloc == urlparse(BASE_URL).netloc:
            continue
        
        if not parsed_url.path.startswith('/news') or parsed_url.path == '/news' or '/article' not in parsed_url.path:
            continue

        urls.add(href)

    await asyncio.to_thread(process_and_save_dataset, urls)

    logger.info('Finished fetching BBC')