from core.classes import get_bot

async def send_to_channel(text: str, channelID: str) -> str:
    try:
        bot = get_bot()
        channel = bot.get_channel(int(channelID)) or await bot.fetch_channel(int(channelID))
        await channel.send(text)
    except Exception as e:
        return f'Error: {str(e)}'