from qdrant_client import models
import logging

from core.functions import settings, qdrant_client

logger = logging.getLogger(__name__)

MAIN_EMBED_MODEL = settings.get('MAIN_EMBED_MODEL')
SUB_EMBED_MODEL = settings.get('SUB_EMBED_MODEL')

class CollectionName:
    databases = "databases"
    user_history = "user_history"
    user_preference = "user_preference"

async def connection():
    '''
    讓全域的 qdrant_client 連線
    '''
    attrs = [getattr(CollectionName, attr) for attr in dir(CollectionName) if not attr.startswith("__")]

    added = []

    for attr in attrs:
        attr = str(attr)
        if not (await qdrant_client.collection_exists(attr)):
            await qdrant_client.create_collection(  
                collection_name=attr,  
                vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE)  
            )

            added.append(attr)

    logger.info(f'新增了 {len(added)} 個 Collection')