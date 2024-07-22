from typing import Annotated

from nonebot import get_driver
from nonebot.adapters import Bot, Event, Message
from nonebot.matcher import Matcher
from nonebot.params import Depends
from nonebot.rule import Rule
from nonebot_plugin_alconna.uniseg import MsgTarget, UniMessage, UniMsg, reply_fetch
from nonebot_plugin_alconna.uniseg.segment import At, Image, Reply, Text
from nonebot_plugin_session import EventSession

from ..context import Context
from ..config import config


def _ExeCodeEnabled() -> Rule:
    global_config = get_driver().config
    try:
        from nonebot.adapters.console import Bot as ConsoleBot
    except ImportError:
        ConsoleBot = None

    def check(bot: Bot, session: EventSession, target: MsgTarget):
        # ConsoleBot 仅有标准输入, 跳过检查
        if ConsoleBot is not None and isinstance(bot, ConsoleBot):
            return True

        # 对于 superuser 和 配置允许的用户, 在任意对话均可触发
        if (session.id1 or "") in (global_config.superusers | config.user):
            return True

        # 当触发对话为群组时, 仅配置允许的群组可触发
        if not target.private and target.id in config.group:
            return True

        return False

    return Rule(check)


def _CodeContext():

    def code_context(session: EventSession) -> Context:
        return Context.get_context(session)

    return Depends(code_context)


def _ExtractCode():

    def extract_code(msg: UniMsg) -> str:
        code = ""
        for seg in msg:
            if isinstance(seg, Text):
                code += seg.text
            elif isinstance(seg, At):
                code += f'"{seg.target}"'
            elif isinstance(seg, Image):
                code += f'"{seg.url or "[url]"}"'

        # 特例：@xxx code print(123)
        #  --> "xxx" code print(123)
        if not code.startswith("code"):
            Matcher.skip()

        return code.removeprefix("code").strip()

    return Depends(extract_code)


def _EventImage():

    async def event_image(msg: UniMsg) -> Image:
        if msg.has(Image):
            return msg[Image, 0]
        elif msg.has(Reply):
            reply = msg[Reply, 0].msg
            if isinstance(reply, Message):
                msg = await UniMessage.generate(message=reply)
                return await event_image(msg)
        Matcher.skip()

    return Depends(event_image)


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


EXECODE_ENABLED: Rule = _ExeCodeEnabled()
CodeContext = Annotated[Context, _CodeContext()]
ExtractCode = Annotated[str, _ExtractCode()]
EventImage = Annotated[Image, _EventImage()]
EventReply = Annotated[Reply, _EventReply()]
EventReplyMessage = Annotated[Message, _EventReplyMessage()]
