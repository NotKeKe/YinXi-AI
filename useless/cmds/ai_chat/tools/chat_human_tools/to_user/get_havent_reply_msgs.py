from core.functions import redis_client

async def get_havent_reply_msgs() -> str:
    return await redis_client.get('chat_human_sent_msgs')