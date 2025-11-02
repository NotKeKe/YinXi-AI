from discord.ext import commands
import logging
import hashlib
import orjson
from openai.types.chat.chat_completion_message_tool_call import ChatCompletionMessageToolCall
from typing import List
from datetime import datetime
from textwrap import dedent

from core.mongodb_clients import MongoDB_DB
from core.qdrant import QdrantCollectionName
from core.functions import current_time

from .call import upsert

from cmds.ai_chat.utils.prompt import get_single_default_system_prompt
from cmds.ai_chat.utils import to_system_message, to_user_message
from cmds.ai_chat.utils.client import AsyncClient

logger = logging.getLogger(__name__)

tool_descrip = [{
    "type": "function",
    "function": {
        "name": "save_to_long_term_memory",
        "description": "調用此工具可將你認為需要存進長期記憶的內容(僅限與使用者相關的內容)，存進資料庫當中",
        "parameters": {
            "type": "object",
            "properties": {
                "userID": { "type": "string", "description": "在此輸入 使用者的ID (user's ID)，確保一字不漏的填入。" },
                "memory": { "type": "string", "description": "在此輸入你希望記住關於使用者的事情，以便於日後回憶。" }
            },
            "required": ["userID", "memory"]
        }
    }
}]

def generate_hash_id(prompt: str, size: int = 10):
    return hashlib.sha256(prompt.encode()).hexdigest()[:size]

async def save_to_long_term_memory(userID: int, memory: str) -> None:
    try:
        userID = int(userID)
    except:
        logger.error('Error accured at save_to_long_term_memory:', exc_info=True)
        return
    
    data = [{
        'text': memory,
        'userID': userID,
        'time': datetime.now().timestamp(),
        'uuid': generate_hash_id(memory)
    }]

    await upsert(data, QdrantCollectionName.user_long_term_memory)

async def long_term_memory(userID: int, user_prompt: str, assistant_prompt: str, exitst_info: str = None, ctx: commands.Context = None):
    system_prompt = await get_single_default_system_prompt('long_term_memory')

    resp = await AsyncClient.self_ollama.chat.completions.create(
        model='qwen3:0.6b-q4_K_M',
        messages=to_system_message(system_prompt) + to_user_message(dedent(f'''
                                                                    請看使用者的prompt，並根據需要調用工具存儲與使用者相關的資訊
                                                                    使用者的ID為: {int(userID)}
                                                                    如果使用者希望存儲已經存儲過的記憶，請不要調用工具
                                                                    已經存在的記憶: ```{exitst_info}```
                                                                    如果不需要調用工具，則只需回答「否」。

                                                                    使用者說: `{user_prompt}`
                                                                    ''').strip()),
        tools=tool_descrip,
        tool_choice='auto'
    )

    async def get_tool_results(tool_calls: List[ChatCompletionMessageToolCall]) -> str:
        try:
            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                if tool_name != 'save_to_long_term_memory': return
                arguments = tool_call.function.arguments
                args = orjson.loads(arguments) if type(arguments) != dict else arguments

                await save_to_long_term_memory(**args)
            logger.info('Save a long_term_memory to vector db')
            if ctx:
                func = ctx.interaction.followup.send if ctx.interaction else ctx.send
                # await func(f'Saved to long_term_memory {f"({args.get('memory', '')})"}', ephemeral=True)
        except: 
            logger.error("Error accured at long_term_memory's function:", exc_info=True)

    if not resp.choices: return
    if not resp.choices[0].message.tool_calls: return
    await get_tool_results(resp.choices[0].message.tool_calls)