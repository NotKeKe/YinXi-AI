from core.classes import get_bot

async def switch_mode(mode: str) -> str:
    from ....on_msg.self_growth import SelfGrowth
    bot = get_bot()
    cog = bot.get_cog('AIChannelTwo')
    self_growth: SelfGrowth = cog.self_growth
    return self_growth.switch_mode(mode)