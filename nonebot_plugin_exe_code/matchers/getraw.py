from nonebot import on_startswith
from nonebot_plugin_alconna.uniseg import UniMessage

from .depends import EXECODE_ENABLED, CodeContext, EventReplyMessage

matcher = on_startswith("getraw", rule=EXECODE_ENABLED)


@matcher.handle()
async def handle_getraw(
    ctx: CodeContext,
    message: EventReplyMessage,
):
    ctx.set_gem(message)
    ctx.set_gurl(await UniMessage.generate(message=message))
    await UniMessage.text(str(message)).send()
