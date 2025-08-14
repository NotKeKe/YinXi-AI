from qdrant_client.models import Filter, MatchValue, FieldCondition

from core.qdrant import QdrantCollectionName
from cmds.vector.call.call import search, delete

async def search_user_long_term_memory(userID: int, query: str, nums: int = 5) -> str:
    ft = Filter(
        must=[
            FieldCondition(
                key='userID', match=MatchValue(value=int(userID))
            )
        ]
    )
    data = await search(query, QdrantCollectionName.user_long_term_memory, ft, nums)

    return '\n'.join([f"<long_term_memory id={d.get('uuid', 'None')} time={d.get('time', 'None')}>{d.get('text', '')}</long_term_memory>" for d in data])

async def delete_user_long_term_memory(userID: int, uuid: str) -> str:
    try:
        ft = Filter(
            must=[
                FieldCondition(
                    key='userID', match=MatchValue(value=int(userID))
                ),
                FieldCondition(
                    key='uuid', match=MatchValue(value=str(uuid))
                )
            ]
        )
        await delete(QdrantCollectionName.user_long_term_memory, ft)
        return f'Succesfully delete a memory ({uuid=})'
    except:
        return f'Failed to delete a memory ({uuid=})'