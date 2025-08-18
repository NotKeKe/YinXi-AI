async def stop_task():
    from cmds.ai_channel_two import aichanneltwo
    if aichanneltwo.keep_think_task:
        aichanneltwo.keep_think_task.cancel()
        return 'Success'
    else:
        return f'無法取消任務，請聯繫管理員'