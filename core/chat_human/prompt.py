from core.functions import redis_client

async def get_current_user_prompt(mode: str) -> str:
    return (await redis_client.get('chat_human_current_user_prompt')) or f'#System: 你現在整處於{mode}，請使用適當工具進行{mode}'

async def add_current_user_prompt(prompt: str):
    await redis_client.set('chat_human_current_user_prompt', prompt)
    await redis_client.expire('chat_human_current_user_prompt', 20)

async def get_current_system_prompt() -> str:
    return (await redis_client.get('chat_human_current_system_prompt')) or ''

async def add_current_system_prompt(prompt: str):
    await redis_client.set('chat_human_current_system_prompt', prompt)