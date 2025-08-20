import orjson
from core.functions import redis_client

async def ignore_msg(channelID: int, msgID: int) -> str:
    data = orjson.loads(await redis_client.get('chat_human_sent_msgs'))
    for item in data[int(channelID)]:
        if item.get('msgID') == str(msgID):
            data[int(channelID)].remove(item)
            break
    await redis_client.set('chat_human_sent_msgs', orjson.dumps(data).decode())
    return f'successfully ignore {msgID=}'