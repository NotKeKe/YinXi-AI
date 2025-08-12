from typing import Tuple, Union, List, Any, Dict
from openai import AsyncOpenAI
from qdrant_client.models import PointStruct, Filter, FilterSelector
import logging
import uuid

from core.mongodb_clients import MongoDB_DB

from ..utils.client import AsyncClient
from ..utils import check_alive
from ..utils.config import MAIN_EMBED_MODEL, SUB_EMBED_MODEL, qdrant_client

logger = logging.getLogger(__name__)

def hash_id(text: str, collection_name: str) -> int:
    namespace = uuid.uuid5(uuid.NAMESPACE_URL, collection_name)
    return int(uuid.uuid5(namespace, text).hex[:12], 16)

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

async def search(query: str, collection_name: str, _filter: Filter | None = None, num: int = 5) -> List[Dict[str, Any]]:
    embedding = (await get_embedding(query))[0]
    points = await qdrant_client.search(
        collection_name=collection_name,
        query_vector=embedding,
        limit=num,
        with_payload=True,
        query_filter=_filter
    )

    return [p.payload or {} for p in points]

async def search_custom_database_uuid(userID: int | str, vector_title: str) -> str:
    data_collection = MongoDB_DB.user_custom_data[str(userID)]
    u = (await data_collection.find_one({'title': vector_title}))['uuid']
    return u

def process_result(data: List[Dict[str, Any]]) -> str:
    """將 payloads 轉為 str 回傳，最終將保留 time 與 text 欄位

    Args:
        data (dict): search 的返回結果
    """    
    d = [f"<database id={index+1}>{f'time: {v.get("time")}' if v.get('time') else ''} {v.get('text')}</database id={index+1}>".strip() for index, v in enumerate(data)]
    return '\n'.join(d)

async def upsert(data: List[Dict[str, Any]], collection_name: str):
    try:
        texts = [item['text'] for item in data]
        embeddings = await get_embedding(texts)

        points = [PointStruct(
                id=hash_id(data[i]['text'] + str(data[i].get('userID', i)), collection_name),
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
    
async def delete(collection_name: str, filter: Filter):
    await qdrant_client.http.points_api.delete_points(
        collection_name=collection_name,
        points_selector=FilterSelector(filter=filter)
    )