from .chat import Chat
import logging

logger = logging.getLogger(__name__)

async def gener_title(history: list, length: int = 15):
    try:
        client = Chat(model='self_ollama:hf.co/keke0130/gemma-3-270m-chinese-title-generator-gguf:F16')
        client.re_system_prompt('')

        # process prompt
        prompt_ls = []
        for h in reversed(history):
            if h.get('role') == 'user':
                content = h.get("content")
                prompt_ls.append(content)
                break

        think, result, complete_history = await client.chat(
            ''.join(prompt_ls),
            is_enable_tools=False,
            if_get_extra_user_info=False,
            temperature=0.1
        )

        return_item = (result[:length]).strip()
        if not return_item:
            for item in reversed(history):
                if item.get('role') == 'user':
                    return_item = item.get('content', 'no_title').strip()
                    break

        return return_item
    except Exception as e:
        logger.error('Error accured at gener_title: ', exc_info=True)
        return None