from core.chat_human.manage_browser import current_pages

async def close_page(uuid: str) -> str:
    if uuid not in current_pages: return f'找不到任何uuid為 `{uuid}` 的page，使用 `call_keke` 聯繫你的主人幫你解決'
    page = current_pages.get(uuid)
    await page.close()