async def switch_mode(mode: str) -> str:
    from ....on_msg.chat_human import self_growth
    return self_growth.switch_mode(mode)