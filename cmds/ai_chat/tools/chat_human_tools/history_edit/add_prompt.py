from core.chat_human.prompt import add_current_user_prompt, add_current_system_prompt
from core.functions import redis_client

async def add_user_prompt(user_prompt: str):
    await add_current_user_prompt(user_prompt)
    return f'已將現在的 user prompt 改為 {user_prompt}'

async def add_system_prompt(system_prompt: str):
    curr_sys_prompt = await redis_client.get('chat_human_current_system_prompt')
    await add_current_system_prompt(system_prompt)
    return f'已將現在的 system prompt 從 ```{curr_sys_prompt}``` 改為 ```{system_prompt}```'