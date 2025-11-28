from chonkie.chunker.semantic import SemanticChunker
from huggingface_hub import login
import os
import time
from typing import Any
from httpx import AsyncClient, Limits
import asyncio
from datasets import load_dataset
import aiofiles
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor

from cmds.vector.call.call import upsert
from core.qdrant import QdrantCollectionName

from .fetch_datas import *
from .fetch_datas.config import JSONL_PATH

from core.functions import yinxi_base_url

LOCK = asyncio.Lock()

def get_chunker():
    # embedding_model 可以直接填 HuggingFace 上的中文模型 ID
    # threshold: 語義相似度閾值 (0~1)，越低切得越碎，中文建議 0.5~0.7 試試
    login(os.getenv("HUGGINGFACE_TOKEN"))
    chunker = SemanticChunker(
        embedding_model="google/embeddinggemma-300m",
        threshold=0.7,                  # 相似度 (0-1). Lower values create more chunks. default:"0.8"
        chunk_size=350,                 # Target number of tokens per chunk (soft limit). default:"512"
        min_sentences_per_chunk=3       # Minimum number of sentences per chunk. default:"1"
    )
    return chunker

def get_rag(text: str, meta: dict[str, Any], chunker) -> list[dict[str, str | int]]:
    # 2. 執行切割
    chunks = chunker([text] if isinstance(text, str) else text)

    texts = set()
    datas = []

    curr_time = datetime.now(timezone(timedelta(hours=8))).isoformat()

    if isinstance(chunks, str): chunks = [chunks]

    for chunk in chunks:
        for c in chunk:
            stripped_text = c.text.strip() # type: ignore
            if stripped_text in texts: continue
            texts.add(stripped_text)
            datas.append({'text': stripped_text, 'meta': {'time': curr_time} | meta | {'token_count': c.token_count}}) # type: ignore

    return datas

async def daily_rag():
    # 清空檔案
    async with aiofiles.open(JSONL_PATH, 'wb') as f:
        pass


    # create client
    limits = Limits(
        max_keepalive_connections=10, 
        max_connections=10
    )
    client = AsyncClient(
        headers={"User-Agent": f"YinXiAIBOT ({yinxi_base_url})"},
        limits=limits
    )


    # fetch datas
    try:
        fetch_tasks = [fetch_bbc, fetch_wiki]
        fetch_tasks = [asyncio.create_task(fetch(client)) for fetch in fetch_tasks]

        await asyncio.gather(*fetch_tasks)
    finally:
        await client.aclose()


    # add to qdrant
    async with LOCK: # 基本上不會發生有併發的問題，但為了避免我哪天手殘 所以還是寫了一下，避免爆記憶體
        with ThreadPoolExecutor(max_workers=2) as executor:
            loop = asyncio.get_running_loop()
            queue = asyncio.Queue(maxsize=150)
            STOP = object() # stop flag

            chunker = await loop.run_in_executor(executor, get_chunker)
            dataset = await loop.run_in_executor(executor, lambda: load_dataset('json', data_files=str(JSONL_PATH), split='train', streaming=True))

            # 模擬 async generator
            # 參考了 https://discuss.python.org/t/running-generators-in-executors-asynchronously/63047/4
            def run_sync(_loop: asyncio.AbstractEventLoop):
                try:
                    for item in dataset:
                        asyncio.run_coroutine_threadsafe(queue.put(item), _loop)
                finally:
                    _loop.call_soon_threadsafe(queue.put_nowait, STOP)

            # 在背景運行
            loop.run_in_executor(executor, run_sync, loop)

            # 為了批量 embedding
            results = []

            # start async generator
            while True:
                item = await queue.get()
                if item is STOP: break

                text = item['text'] # type: ignore
                meta = item['meta'] # type: ignore
                assert isinstance(text, str)
                assert isinstance(meta, dict)

                result = await loop.run_in_executor(executor, get_rag, text, meta, chunker)
                results += result

                # 批量寫入
                if len(results) >= 100:
                    await upsert(results, QdrantCollectionName.daily_rag) # type: ignore
                    results = []

                await asyncio.sleep(0.05)

            try:
                del chunker
            except Exception as e:
                print('Cannot del chunker: ', e)
