from qdrant_client import models

from core.functions import settings, qdrant_client

MAIN_EMBED_MODEL = settings.get('MAIN_EMBED_MODEL')
SUB_EMBED_MODEL = settings.get('SUB_EMBED_MODEL')

async def connection():
    await qdrant_client.create_collection(  
        collection_name="async_collection",  
        vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE)  
    )