import contextlib
from io import BytesIO
from typing import Annotated

from nonebot import on_startswith, require
from nonebot.adapters import Bot, Event
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata
from nonebot.plugin.load import inherit_supported_adapters
from PIL.Image import open as Image_open

requirements = {
    "nonebot_plugin_alconna",
    "nonebot_plugin_datastore",
    "nonebot_plugin_session",
    "nonebot_plugin_userinfo",
}
[require(i) for i in requirements]
from nonebot_plugin_alconna.uniseg import UniMessage, image_fetch
from nonebot_plugin_session import EventSession
from nonebot_plugin_userinfo import EventUserInfo, UserInfo

from .code_context import Context
from .config import Config
from .depends import (
    EXECODE_ENABLED,
    CodeContext,
    EventImage,
    EventReply,
    EventReplyMessage,
    EventTarget,
    ExtractCode,
)

__version__ = "1.0.0"
__plugin_meta__ = PluginMetadata(
    name="exe_code",
    description="在对话中执行 Python 代码",
    usage="code {Your code here...}",
    type="application",
    homepage="https://github.com/wyf7685/nonebot-plugin-exe-code",
    config=Config,
    supported_adapters=inherit_supported_adapters(*requirements),
    extra={
        "author": "wyf7685",
        "version": __version__,
    },
)


code_exec = on_startswith("code", rule=EXECODE_ENABLED)
code_getraw = on_startswith("getraw", rule=EXECODE_ENABLED)
code_getmid = on_startswith("getmid", rule=EXECODE_ENABLED)
code_getimg = on_startswith("getimg", rule=EXECODE_ENABLED)
code_terminate = on_startswith("terminate", rule=EXECODE_ENABLED, permission=SUPERUSER)


@code_exec.handle()
async def handle_exec(
    bot: Bot,
    session: EventSession,
    code: ExtractCode,
    uinfo: Annotated[UserInfo, EventUserInfo()],
):
    try:
        await Context.execute(bot, session, code)
    except Exception as e:
        text = f"用户{uinfo.user_name}({uinfo.user_id}) 执行代码时发生错误: {e}"
        logger.opt(exception=True).warning(text)
        await UniMessage.text(f"执行失败: {e!r}").send()


@code_getraw.handle()
async def handle_getraw(
    ctx: CodeContext,
    message: EventReplyMessage,
):
    ctx.set_gem(message)
    ctx.set_gurl(await UniMessage.generate(message=message))
    await UniMessage.text(str(message)).send()


@code_getmid.handle()
async def handle_getmid(
    ctx: CodeContext,
    reply: EventReply,
    reply_msg: EventReplyMessage,
):
    ctx.set_gem(reply_msg)
    ctx.set_gurl(await UniMessage.generate(message=reply_msg))
    await UniMessage.text(reply.id).send()


@code_getimg.handle()
async def handle_getimg(
    bot: Bot,
    event: Event,
    ctx: CodeContext,
    matcher: Matcher,
    image: EventImage,
):
    varname = event.get_message().extract_plain_text().removeprefix("getimg").strip()
    if (varname := varname or "img") and not varname.isidentifier():
        await matcher.finish(f"{varname} 不是一个合法的 Python 标识符")

    try:
        img_bytes = await image_fetch(event, bot, {}, image)
        if not isinstance(img_bytes, bytes):
            raise ValueError(f"获取图片数据类型错误: {type(img_bytes)!r}")
    except Exception as err:
        await matcher.finish(f"保存图片时出错: {err}")

    ctx.set_gurl(image)
    ctx.set_value(varname, Image_open(BytesIO(img_bytes)))
    await matcher.finish(f"图片已保存至变量 {varname}")


@code_terminate.handle()
async def handle_terminate(target: EventTarget):
    with contextlib.suppress(KeyError):
        if Context.get_context(target).cancel():
            await UniMessage("中止").at(target).text("的执行任务").send()
