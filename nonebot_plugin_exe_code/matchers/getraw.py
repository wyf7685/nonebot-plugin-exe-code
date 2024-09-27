from typing import NoReturn

from nonebot import on_message
from nonebot_plugin_alconna.uniseg import UniMessage

from .depends import AllowExeCode, CodeContext, EventReplyMessage, startswith

matcher = on_message(startswith("getraw"), permission=AllowExeCode)


@matcher.handle()
async def handle_getraw(
    ctx: CodeContext,
    message: EventReplyMessage,
) -> NoReturn:
    async with ctx.lock():
        ctx.set_gem(message)
        ctx.set_gurl(await UniMessage.generate(message=message))
    await UniMessage.text(str(message)).finish()
