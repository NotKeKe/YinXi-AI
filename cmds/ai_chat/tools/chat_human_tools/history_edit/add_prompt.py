from core.chat_human.prompt import add_current_user_prompt, add_current_system_prompt

async def add_user_prompt(user_prompt: str):
    await add_current_user_prompt(user_prompt)
    return f'已將現在的 user prompt 改為 {user_prompt}'

async def add_system_prompt(system_prompt: str):
    await add_current_system_prompt(system_prompt)
    return f'已將現在的 system prompt 改為 {system_prompt}'