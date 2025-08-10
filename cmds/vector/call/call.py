from typing import Tuple, Union, List
from openai import AsyncOpenAI

from ..utils.client import AsyncClient
from ..utils import connected
from ..utils.config import MAIN_EMBED_MODEL, SUB_EMBED_MODEL, qdrant_client

# TODO

def model_select() -> Tuple[AsyncOpenAI, str]:
    """Return AsyncOpenAI and model

    Returns:
        Tuple[AsyncOpenAI, str]: _description_
    """    
    if connected:
        client = AsyncClient.lmstudio
        model = MAIN_EMBED_MODEL
    else:
        client = AsyncClient.self_ollama
        model = SUB_EMBED_MODEL
    return client, model

async def search(query: str) -> list[str]:
    client, model = model_select()

    resp = await client.embeddings.create(
        input=query,
        model=model
    )
    embedding = resp.data[0].embedding

async def insert(query: Union[list[str], str]):
    ...