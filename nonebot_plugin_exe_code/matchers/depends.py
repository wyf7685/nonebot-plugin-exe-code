import contextlib
from typing import Annotated

from nonebot.adapters import Bot, Event, Message
from nonebot.matcher import Matcher
from nonebot.params import Depends
from nonebot.permission import SUPERUSER, Permission
from nonebot.rule import Rule
from nonebot_plugin_alconna.uniseg import UniMessage, UniMsg, reply_fetch
from nonebot_plugin_alconna.uniseg.segment import At, Image, Reply, Text
from nonebot_plugin_session import EventSession

from ..config import config
from ..context import Context


def _AllowExeCode() -> Permission:
    def check_console(bot: Bot) -> bool:  # pragma: no cover
        return False

    with contextlib.suppress(ImportError):
        from nonebot.adapters.console import Bot as ConsoleBot

        def check_console(bot: Bot) -> bool:
            return isinstance(bot, ConsoleBot)

    async def check(bot: Bot, session: EventSession) -> bool:
        # ConsoleBot 仅有标准输入, 跳过检查
        if check_console(bot):
            return True

        # 对于 superuser 和 配置允许的用户, 在任意对话均可触发
        if (session.id1 or "") in config.user:
            return True

        # 当触发对话为群组时, 仅配置允许的群组可触发
        if session.id2 is not None and session.id2 in config.group:
            return True

        return False

    return SUPERUSER | check


def _CodeContext():
    async def code_context(session: EventSession) -> Context:
        return Context.get_context(session)

    return Depends(code_context)


def _ExtractCode():
    async def extract_code(msg: UniMsg) -> str:
        code = ""
        for seg in msg:
            if isinstance(seg, Text):
                code += seg.text
            elif isinstance(seg, At):
                code += f'"{seg.target}"'
            elif isinstance(seg, Image):
                code += f'"{seg.url or "[url]"}"'

        code = code.strip()

        # 特例：@xxx code print(123)
        #  --> "xxx" code print(123)
        if not code.startswith("code"):
            Matcher.skip()

        return code.removeprefix("code").strip()

    return Depends(extract_code)


def _EventImage():
    async def event_image(msg: UniMessage, _in_reply: bool = False) -> Image:
        if msg.has(Image):
            return msg[Image, 0]
        elif msg.has(Reply) and not _in_reply:
            reply = msg[Reply, 0].msg
            if isinstance(reply, Message):
                msg = await UniMessage.generate(message=reply)
                return await event_image(msg, True)

        Matcher.skip()

    async def dependency(msg: UniMsg) -> Image:
        return await event_image(msg)

    return Depends(dependency)


def _EventReply():
    async def event_reply(event: Event, bot: Bot) -> Reply:
        if reply := await reply_fetch(event, bot):
            return reply
        Matcher.skip()

    return Depends(event_reply)


def _EventReplyMessage():
    async def event_reply_message(event: Event, reply: EventReply) -> Message:
        if not (msg := reply.msg):
            Matcher.skip()

        if not isinstance(msg, Message):
            msg = type(event.get_message())(msg)

        return msg

    return Depends(event_reply_message)


def startswith(text: str):
    def starts_checker(event: Event):
        try:
            msg = event.get_message()
        except NotImplementedError:
            Matcher.skip()

        return msg.extract_plain_text().strip().startswith(text)

    return Rule(starts_checker)


AllowExeCode: Permission = _AllowExeCode()
CodeContext = Annotated[Context, _CodeContext()]
ExtractCode = Annotated[str, _ExtractCode()]
EventImage = Annotated[Image, _EventImage()]
EventReply = Annotated[Reply, _EventReply()]
EventReplyMessage = Annotated[Message, _EventReplyMessage()]
