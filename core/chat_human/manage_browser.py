from playwright.async_api import async_playwright, Browser, Playwright, Page
import logging
from datetime import datetime

from core.functions import redis_client

_global_browser: Browser = None
_playwright_instance: Playwright = None

current_pages: dict[str, Page] = {}

logger = logging.getLogger(__name__)

async def get_browser() -> Browser:
    global _global_browser, _playwright_instance
    if not _global_browser:
        _playwright_instance = await async_playwright().start()
        _global_browser = await _playwright_instance.chromium.launch(headless=True)
        logger.info('已創建 browser 實例')
    return _global_browser

async def add_page(uuid: str, page: Page):
    current_pages[uuid] = page
    await redis_client.hset('chat_human_browser', uuid, str({'url': page.url, 'createAt': datetime.now().timestamp()}))

async def close_browser():
    global _global_browser, _playwright_instance
    if _global_browser:
        await _global_browser.close()
        _global_browser = None
        logger.info('已關閉 browser 實例')
    if _playwright_instance:
        await _playwright_instance.stop()
        _playwright_instance = None
        logger.info('已關閉 playwright 實例')