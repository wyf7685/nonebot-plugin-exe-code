from nonebot import on_startswith
from nonebot_plugin_alconna.uniseg import UniMessage

from .depends import AllowExeCode, CodeContext, EventReplyMessage

matcher = on_startswith("getraw", permission=AllowExeCode)


@matcher.handle()
async def handle_getraw(
    ctx: CodeContext,
    message: EventReplyMessage,
):
    ctx.set_gem(message)
    ctx.set_gurl(await UniMessage.generate(message=message))
    await UniMessage.text(str(message)).finish()
