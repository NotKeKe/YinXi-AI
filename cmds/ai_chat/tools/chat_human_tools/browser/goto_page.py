from playwright.async_api import async_playwright
import uuid

from core.chat_human.manage_browser import get_browser, add_page

async def goto_page(url: str) -> str:
    browser = await get_browser()
    page = await browser.new_page()
    await page.goto(url, wait_until="domcontentloaded")
    u = str(uuid.uuid4())

    await add_page(u, page)
    
    return f'成功進入page (uuid: {u})'