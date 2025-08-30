from core.classes import get_bot

async def send_to_channel(text: str, channelID: str, replied: bool = False, messageID: str = None) -> str:
    try:
        if replied and not messageID:
            return f'你應該提供 messageID 參數，才能使用 reply 回覆訊息。'
        
        bot = get_bot()
        channel = bot.get_channel(int(channelID)) or await bot.fetch_channel(int(channelID))
        if replied:
            msg = await channel.fetch_message(int(messageID))
            await msg.reply(text)
        else:
            await channel.send(text)
    except Exception as e:
        return f'Error: {str(e)}'