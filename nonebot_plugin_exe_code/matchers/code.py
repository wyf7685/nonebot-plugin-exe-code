from typing import Annotated

from nonebot import on_startswith
from nonebot.adapters import Bot
from nonebot.log import logger
from nonebot_plugin_alconna.uniseg import UniMessage
from nonebot_plugin_session import EventSession
from nonebot_plugin_userinfo import EventUserInfo, UserInfo

from ..context import Context
from .depends import EXECODE_ENABLED, ExtractCode

matcher = on_startswith("code", rule=EXECODE_ENABLED)


@matcher.handle()
async def handle_code(
    bot: Bot,
    session: EventSession,
    code: ExtractCode,
    uinfo: Annotated[UserInfo, EventUserInfo()],
):
    try:
        await Context.execute(bot, session, code)
    except BaseException as err:
        text = f"用户{uinfo.user_name}({uinfo.user_id}) 执行代码时发生错误: {err}"
        logger.opt(exception=err).warning(text)
        await UniMessage.text(f"执行失败: {err!r}").send()
