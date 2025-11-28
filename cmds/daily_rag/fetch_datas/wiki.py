from pathlib import Path
from datetime import datetime
from httpx import AsyncClient
from datasets import load_dataset
import asyncio
import aiofiles
import orjson
import logging

logger = logging.getLogger(__name__)

from .config import JSONL_PATH

CURRENT_DIR = Path(__file__).parent
last_modified_file = CURRENT_DIR / 'last_modified.txt'
last_modified_file.touch(exist_ok=True)

with open(last_modified_file, 'r', encoding='utf-8') as f:
    try:
        last_modified: datetime = datetime.fromisoformat(f.read())
    except:
        last_modified = datetime.fromisoformat('1999-11-11T11:11:11+00:00')

repo_name = 'yuhuanstudio/wikipedia-pretrain-zh-tw'

def process_and_save_dataset(last_modified_iso: str):
    dataset = load_dataset(repo_name, split='train', streaming=True)
    
    with open(JSONL_PATH, 'ab', buffering=1024*1024*4) as f:
        meta = {
            'url': f'https://huggingface.co/datasets/{repo_name}',
            'time': last_modified_iso
        }
        
        for ex in dataset:
            record = {
                'text': ex['text'], # type: ignore
                'meta': meta
            }
            f.write(orjson.dumps(record) + b'\n')

async def fetch_wiki(client: AsyncClient):
    logger.info('Fetching Wiki')
    response = await client.get(f'https://huggingface.co/api/datasets/{repo_name}')
    data = response.json()
    lastModified = datetime.fromisoformat(data['lastModified'])
    if lastModified <= last_modified: return

    del data
    await asyncio.to_thread(
        process_and_save_dataset, 
        last_modified_iso=lastModified.isoformat()
    )

    async with aiofiles.open(last_modified_file, 'w', encoding='utf-8') as f:
        await f.write(lastModified.isoformat())

    logger.info(f'Finished fetching Wiki')