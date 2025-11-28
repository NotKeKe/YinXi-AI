from core.qdrant import QdrantCollectionName
from cmds.vector.call.call import search
from cmds.ai_chat.chat.chat import Chat

tool_descrip = [{
    "type": "function",
    "function": {
        "name": "local_search",
        "description": "The tool is used to search some datas from trusted resources.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": { "type": "string", "description": "Enter the query here." }
            },
            "required": ["query"]
        }
    }
}]

async def local_search(query: str) -> str:
    results = await search(query, QdrantCollectionName.daily_rag, num=10)
    return '\n'.join(f'<local_search index={i} time={r.get('time')}> {r.get("text")} </local_search index={i}>' for i, r in enumerate(results))

async def ask_ai(query: str, model: str = 'lmstudio:gpt-oss-20b') -> tuple[str, str]:
    chat = Chat(model=model)
    
    think, content, history = await chat.chat(
        prompt=query,
        tool_choice='required',
        custom_tool_description=tool_descrip,
        custom_tools={
            'local_search': local_search
        }
    )

    return think, content