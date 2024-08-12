import contextlib
import itertools
from datetime import datetime
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from nonebot.adapters import Bot, Event
    from nonebot.adapters.console import MessageEvent as ConsoleMessageEvent
    from nonebot.adapters.onebot.v11 import Bot as V11Bot
    from nonebot.adapters.onebot.v11 import GroupMessageEvent as V11GroupMessageEvent
    from nonebot.adapters.onebot.v11 import Message as V11Message
    from nonebot.adapters.onebot.v11 import (
        PrivateMessageEvent as V11PrivateMessageEvent,
    )
    from nonebot.adapters.qq import MessageCreateEvent as QQMessageCreateEvent


def _faker(gen: "itertools.count[int]"):
    def faker():
        return next(gen)

    return faker


fake_user_id = _faker(itertools.count(100))
fake_group_id = _faker(itertools.count(200))
fake_img_bytes = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```"
    b"\x00\x00\x00\x04\x00\x01\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82"
)


def fake_v11_group_message_event(**field) -> "V11GroupMessageEvent":
    from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message
    from nonebot.adapters.onebot.v11.event import Sender
    from pydantic import create_model

    _Fake = create_model("_Fake", __base__=GroupMessageEvent)

    class FakeEvent(_Fake):
        time: int = 1000000
        self_id: int = 1
        post_type: Literal["message"] = "message"
        sub_type: str = "normal"
        user_id: int = 10
        message_type: Literal["group"] = "group"
        group_id: int = 10000
        message_id: int = 1
        message: Message = Message("test")
        raw_message: str = "test"
        font: int = 0
        sender: Sender = Sender(
            card="",
            nickname="test",
            role="member",
        )
        to_me: bool = False

    return FakeEvent(**field)


def fake_v11_private_message_event(**field) -> "V11PrivateMessageEvent":
    from nonebot.adapters.onebot.v11 import Message, PrivateMessageEvent
    from nonebot.adapters.onebot.v11.event import Sender
    from pydantic import create_model

    _Fake = create_model("_Fake", __base__=PrivateMessageEvent)

    class FakeEvent(_Fake):
        time: int = 1000000
        self_id: int = 1
        post_type: Literal["message"] = "message"
        sub_type: str = "friend"
        user_id: int = 10
        message_type: Literal["private"] = "private"
        message_id: int = 1
        message: Message = Message("test")
        raw_message: str = "test"
        font: int = 0
        sender: Sender = Sender(nickname="test")
        to_me: bool = False

    return FakeEvent(**field)


def fake_console_message_event(**field) -> "ConsoleMessageEvent":
    from nonebot.adapters.console import Message, MessageEvent, User
    from pydantic import create_model

    _Fake = create_model("_Fake", __base__=MessageEvent)

    class FakeEvent(_Fake):
        time: datetime = datetime.now()
        self_id: str = "pytest"
        post_type: Literal["message"] = "message"
        user: User = User("nonebug")
        message: Message = Message()

    return FakeEvent(**field)


def fake_qq_message_create_event(**field) -> "QQMessageCreateEvent":
    from nonebot.adapters.qq import MessageCreateEvent
    from nonebot.adapters.qq.models.common import (
        MessageArk,
        MessageAttachment,
        MessageEmbed,
        MessageReference,
    )
    from nonebot.adapters.qq.models.guild import Member, User
    from pydantic import create_model

    _Fake = create_model("_Fake", __base__=MessageCreateEvent)

    class FakeEvent(_Fake):
        id: str = "1"
        channel_id: str = "20000"
        guild_id: str = "30000"
        content: str | None = None
        timestamp: datetime | None = None
        edited_timestamp: datetime | None = None
        mention_everyone: bool | None = None
        author: User = User(id="10000")
        attachments: list[MessageAttachment] | None = None
        embeds: list[MessageEmbed] | None = None
        mentions: list[User] | None = None
        member: Member | None = None
        ark: MessageArk | None = None
        seq: int | None = None
        seq_in_channel: str | None = None
        message_reference: MessageReference | None = None
        src_guild_id: str | None = None

    return FakeEvent(**field)


def fake_v11_group_exe_code(
    group_id: int, user_id: int, code: "str | V11Message"
) -> "V11GroupMessageEvent":
    from nonebot.adapters.onebot.v11 import MessageSegment

    event = fake_v11_group_message_event(
        group_id=group_id,
        user_id=user_id,
        message=MessageSegment.text("code ") + code,
    )
    return event


def fake_v11_private_exe_code(
    user_id: int, code: "str | V11Message"
) -> "V11PrivateMessageEvent":
    from nonebot.adapters.onebot.v11 import MessageSegment

    event = fake_v11_private_message_event(
        user_id=user_id,
        message=MessageSegment.text("code ") + code,
    )
    return event


def fake_qq_guild_exe_code(
    user_id: str, channel_id: str, guild_id: str, code: str
) -> "QQMessageCreateEvent":
    from nonebot.adapters.qq.models.guild import User

    event = fake_qq_message_create_event(
        channel_id=channel_id,
        guild_id=guild_id,
        user=User(id=user_id),
        content=f"code {code}",
    )
    return event


def fake_v11_event_session(
    bot: "V11Bot",
    user_id: int | None = None,
    group_id: int | None = None,
):
    from nonebot.adapters.onebot.v11 import Message
    from nonebot_plugin_session import extract_session

    user_id = user_id or fake_user_id()
    message = Message()
    if group_id is not None:
        event = fake_v11_group_message_event(
            user_id=user_id, group_id=group_id, message=message
        )
    else:
        event = fake_v11_private_message_event(user_id=user_id, message=message)
    session = extract_session(bot, event)
    return event, session


@contextlib.contextmanager
def ensure_context(bot: "Bot", event: "Event"):
    # ref: `nonebot.internal.matcher.matcher:Matcher.ensure_context`
    from nonebot.internal.matcher import current_bot, current_event

    b = current_bot.set(bot)
    e = current_event.set(event)

    try:
        yield
    finally:
        current_bot.reset(b)
        current_event.reset(e)
