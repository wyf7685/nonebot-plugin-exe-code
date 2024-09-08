from typing import Annotated

from nonebot import on_startswith
from nonebot.adapters import Bot, Event
from nonebot.log import logger
from nonebot_plugin_alconna.uniseg import UniMessage
from nonebot_plugin_session import EventSession
from nonebot_plugin_userinfo import EventUserInfo, UserInfo

from ..context import Context
from .depends import AllowExeCode, ExtractCode

matcher = on_startswith("code", permission=AllowExeCode)


@matcher.handle()
async def handle_code(
    bot: Bot,
    event: Event,
    session: EventSession,
    code: ExtractCode,
    uinfo: Annotated[UserInfo | None, EventUserInfo()],
):
    try:
        await Context.execute(bot, session, code)
    except BaseException as err:
        name = (
            event.get_user_id()
            if uinfo is None
            else f"{uinfo.user_name}({uinfo.user_id})"
        )
        logger.opt(exception=err).warning(f"用户 {name} 执行代码时发生错误: {err}")
        await UniMessage.text(f"执行失败: {err!r}").send()
    await matcher.finish()
