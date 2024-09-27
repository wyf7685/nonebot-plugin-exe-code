from typing import NoReturn

from nonebot import on_message
from nonebot_plugin_alconna.uniseg import UniMessage

from .depends import (
    AllowExeCode,
    CodeContext,
    EventReply,
    EventReplyMessage,
    startswith,
)

matcher = on_message(startswith("getmid"), permission=AllowExeCode)


@matcher.handle()
async def handle_getmid(
    ctx: CodeContext,
    reply: EventReply,
    reply_msg: EventReplyMessage,
) -> NoReturn:
    async with ctx.lock():
        ctx.set_gem(reply_msg)
        ctx.set_gurl(await UniMessage.generate(message=reply_msg))
    await UniMessage.text(reply.id).finish()
