import aiofiles

async def read(path: str) -> str:
    try:
        if not path.startswith('./data/temp'): return '目前僅能存取 `./data/temp` 底下的資訊'
        async with aiofiles.open(path, 'r', encoding='utf-8') as f:
            return await f.read()
    except Exception as e:
        return f'Error: {str(e)}'