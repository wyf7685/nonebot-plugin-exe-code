from nonebot import on_startswith
from nonebot_plugin_alconna.uniseg import UniMessage

from .depends import EXECODE_ENABLED, CodeContext, EventReply, EventReplyMessage

matcher = on_startswith("getmid", rule=EXECODE_ENABLED)


@matcher.handle()
async def handle_getmid(
    ctx: CodeContext,
    reply: EventReply,
    reply_msg: EventReplyMessage,
):
    ctx.set_gem(reply_msg)
    ctx.set_gurl(await UniMessage.generate(message=reply_msg))
    await UniMessage.text(reply.id).send()
