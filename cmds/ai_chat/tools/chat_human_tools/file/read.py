import aiofiles

async def read(path: str) -> str:
    try:
        async with aiofiles.open(path, 'r', encoding='utf-8') as f:
            return await f.read()
    except Exception as e:
        return f'Error: {str(e)}'