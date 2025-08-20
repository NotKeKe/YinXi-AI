async def switch_mode(mode: str, rest_time: int = 300) -> str:
    from ....on_msg.chat_human import self_growth
    return self_growth.switch_mode(mode, rest_time)