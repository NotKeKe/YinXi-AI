from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .information import Info

async def send_message(info: 'Info', content: str, tag_user: bool = False, save_to_info: bool = True):
    '''
    msg 會存回 info
    tag_user: (default to False) 標記使用者。
        * 會直接 tag 在訊息的開頭
    '''
    if not info.msg: return
    user = info.msg.author
    
    msg = await info.ctx.send(f"{f'{user.mention} ' if tag_user else ''}{content}")

    if save_to_info:
        info.msg = msg

async def edit_message(info: 'Info', content: str, tag_user: bool = False):
    '''
    msg 會存回 info
    tag_user: (default to False) 標記使用者。
        * 會另外發送一則訊息 tag user
    '''
    if not info.msg: return
    user = info.msg.author
    info.msg = await info.msg.edit(content=content)
    if tag_user:
        await info.ctx.send(f'{user.mention}')