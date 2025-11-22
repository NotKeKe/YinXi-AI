import logging

from cmds.vector.utils.check_alive import get_connection_status
from .chat import Chat

logger = logging.getLogger(__name__)

async def select_model() -> str:
    status = await get_connection_status()
    return '' if status else 'self_ollama:hf.co/keke0130/gemma-3-270m-chinese-title-generator-gguf:F16'

def get_last_user_input(history: list) -> str:
    for h in reversed(history):
        if h.get('role') == 'user':
            item = h.get('content', '').strip()
            break
        
    return item or 'no_title'

async def gener_title(history: list, length: int = 15) -> str:
    try:
        model = await select_model()
        last_user_prompt = get_last_user_input(history)

        if not model or len(last_user_prompt) <= length: # 模型無法連接 or 使用者 prompt 本來就很短
            return last_user_prompt[:length]
        
        client = Chat(model='self_ollama:hf.co/keke0130/gemma-3-270m-chinese-title-generator-gguf:F16')
        client.re_system_prompt('')


        think, result, complete_history = await client.chat(
            last_user_prompt,
            is_enable_tools=False,
            if_get_extra_user_info=False,
            temperature=0.1
        )

        return_item = (result[:length]).strip()
        if not return_item:
            return_item = last_user_prompt[:length]

        return return_item
    except Exception as e:
        logger.error('Error accured at gener_title: ', exc_info=True)
        return ''