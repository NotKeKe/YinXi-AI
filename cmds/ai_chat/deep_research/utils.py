from typing import TYPE_CHECKING, Any
import chromadb
import asyncio
import uuid

from cmds.vector.call.call import get_embedding

if TYPE_CHECKING:
    from .information import Info

async def send_message(info: 'Info', content: str, tag_user: bool = False, save_to_info: bool = True):
    '''
    msg 會存回 info
    tag_user: (default to False) 標記使用者。
        * 會直接 tag 在訊息的開頭
    '''
    if not info.msg: return
    user = info.msg.author
    
    msg = await info.ctx.send(f"{f'{user.mention} ' if tag_user else ''}{content}")

    if save_to_info:
        info.msg = msg

async def edit_message(info: 'Info', content: str, tag_user: bool = False):
    '''
    msg 會存回 info
    tag_user: (default to False) 標記使用者。
        * 會另外發送一則訊息 tag user
    '''
    if not info.msg: return
    user = info.msg.author
    info.msg = await info.msg.edit(content=content)
    if tag_user:
        await info.ctx.send(f'{user.mention}')

class _TempVector:
    def __init__(self):
        self.client = chromadb.Client()

    def _gener_ids(self, num: int) -> list[str]:
        ids = [str(uuid.uuid4()) for _ in range(num)]
        return ids

    def _add(self, coll_name: str, documents: list[str], embeddings: list[list[float]], metadatas: list[dict[str, Any]]):
        self.client.get_or_create_collection(name=coll_name).add(
            embeddings=embeddings, # type: ignore
            documents=documents, # type: ignore
            metadatas=metadatas, # type: ignore
            ids=self._gener_ids(len(documents))
        )

    def _query(self, coll_name: str, embedding: list[float], num: int = 5) -> list[dict[str, Any]]:
        return self.client.get_or_create_collection(name=coll_name).query(
            query_embeddings=[embedding], # type: ignore
            n_results=num
        )

    def _del_coll(self, coll_name: str):
        self.client.get_or_create_collection(name=coll_name).delete()

    async def add(self, coll_name: str, documents: list[str], metadatas: list[dict[str, Any]]):
        embeddings = await get_embedding(documents)
        await asyncio.to_thread(self._add, coll_name, documents, embeddings, metadatas)

    async def query(self, coll_name: str, query: str, num: int = 5) -> list[dict[str, Any]]:
        embedding = (await get_embedding(query))[0]
        return await asyncio.to_thread(self._query, coll_name, embedding, num)

    async def del_coll(self, coll_name: str):
        await asyncio.to_thread(self._del_coll, coll_name)

    async def get_collection_names(self) -> list[str]:
        collections = await asyncio.to_thread(self.client.list_collections)
        return [collection.name for collection in collections]
    
TempVector = _TempVector()