from core.classes import get_bot
from core.functions import KeJCID

async def call_keke(query: str) -> str:
    bot = get_bot()
    user = bot.get_user(int(KeJCID)) or await bot.fetch_user(int(KeJCID))

    await user.send(query)
    return '已成功傳送訊息給克克，請耐心等待，稍後會在聊天歷史中看到對話'