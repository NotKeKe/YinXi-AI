from datetime import datetime

from cmds.vector.call.call import search, upsert

from core.qdrant import QdrantCollectionName
from core.functions import UnixToReadable

async def save(text: str) -> str:
    try:
        await upsert([{'text': text, 'time': datetime.now().timestamp()}], QdrantCollectionName.self_growth_database)
        return f'已成功存儲進向量知識庫當中'
    except Exception as e:
        return f'存儲失敗，請聯繫管理員 (Error: {e})'
    
async def _search(query: str, num: int = 3) -> str:
    try:
        result = await search(query, QdrantCollectionName.self_growth_database, num=num)
        return '\n'.join([f'<database_search_result index={i} time={UnixToReadable(r.get('time'))}>{r.get('text')}</database_search_result index={i}>' for i, r in enumerate(result)]) if result else '沒有找到任何結果'
    except Exception as e:
        return f'搜尋失敗，請聯繫管理員 (Error: {e})'