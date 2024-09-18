from typing import NoReturn

from nonebot import on_message
from nonebot.adapters import Bot, Event
from nonebot.log import logger
from nonebot_plugin_alconna.uniseg import UniMessage
from nonebot_plugin_session import EventSession

from ..context import Context
from .depends import AllowExeCode, ExtractCode, startswith

matcher = on_message(startswith("code"), permission=AllowExeCode)


@matcher.handle()
async def handle_code(
    bot: Bot,
    event: Event,
    session: EventSession,
    code: ExtractCode,
) -> NoReturn:
    try:
        await Context.execute(bot, session, code)
    except BaseException as err:
        msg = f"用户 {event.get_user_id()} 执行代码时发生错误: {err}"
        logger.opt(exception=err).warning(msg)
        await UniMessage.text(f"执行失败: {err!r}").send()
    await matcher.finish()
