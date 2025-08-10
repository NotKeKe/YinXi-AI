from typing import Tuple, Union, List, Any, Dict
from openai import AsyncOpenAI
import hashlib
from qdrant_client.models import PointStruct, Filter
import logging

from ..utils.client import AsyncClient
from ..utils import check_alive
from ..utils.config import MAIN_EMBED_MODEL, SUB_EMBED_MODEL, qdrant_client

logger = logging.getLogger(__name__)

# TODO

def hash_id(text: str) -> int:
    return int(hashlib.sha256(text.encode('utf-8')).hexdigest(), 16) % (10**12)

async def get_embedding(text: Union[List[str], str]) -> List[List[float]]:
    client, model = model_select()

    if isinstance(text, str):
        text = [text]

    resp = await client.embeddings.create(
        input=text,
        model=model
    )
    embeddings = [data.embedding for data in resp.data]
    return embeddings

def model_select() -> Tuple[AsyncOpenAI, str]:
    """Return AsyncOpenAI and model

    Returns:
        Tuple[AsyncOpenAI, str]: _description_
    """    
    if check_alive.connected:
        client = AsyncClient.lmstudio
        model = MAIN_EMBED_MODEL
    else:
        client = AsyncClient.self_ollama
        model = SUB_EMBED_MODEL
    return client, model

async def search(query: str, collection_name: str, _filter: Filter = None) -> List[Dict[str, Any]]:
    embedding = (await get_embedding(query))[0]
    points = await qdrant_client.search(
        collection_name=collection_name,
        query_vector=embedding,
        limit=5,
        with_payload=True,
        query_filter=_filter
    )

    return [p.payload or {} for p in points]

async def upsert(data: List[Dict[str, Any]], collection_name: str):
    try:
        texts = [item['text'] for item in data]
        embeddings = await get_embedding(texts)

        points = [PointStruct(
                id=hash_id(data[i]['text'] + str(data[i].get('userID', i))),
                vector=embeddings[i],
                payload=data[i]
            )
            for i in range(len(embeddings))
        ]

        await qdrant_client.upsert(
            collection_name=collection_name,
            points=points
        )

        return True
    except:
        logger.error('Error accured while upserting data', exc_info=True)
        return False