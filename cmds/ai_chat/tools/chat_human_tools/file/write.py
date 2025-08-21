import aiofiles

async def write(content: str, path: str) -> str:
    try:
        if not path.startswith('./data/temp'): return '目前僅能存取 `./data/temp` 底下的資訊'
        async with aiofiles.open(path, 'a', encoding='utf-8') as f:
            await f.write(content)
            return '已成功寫入檔案'
    except Exception as e:
        return f'Error: {str(e)}'