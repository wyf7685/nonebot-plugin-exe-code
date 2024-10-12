# ruff: noqa: N806

from typing import TYPE_CHECKING, Any, Literal, overload

from nonebot.adapters.onebot.v11 import (
    Adapter,
    Bot,
    GroupMessageEvent,
    Message,
    MessageSegment,
    PrivateMessageEvent,
)
from nonebot.adapters.onebot.v11.event import Sender
from nonebug.mixin.call_api import ApiContext
from nonebug.mixin.process import MatcherContext
from pydantic import create_model

from .common import fake_bot, fake_user_id

if TYPE_CHECKING:
    from nonebot_plugin_session import Session


def fake_v11_bot(ctx: ApiContext | MatcherContext, **kwargs: Any) -> Bot:
    return fake_bot(ctx, Adapter, Bot, **kwargs)


def fake_v11_group_message_event(**field: Any) -> GroupMessageEvent:
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


def fake_v11_private_message_event(**field: Any) -> PrivateMessageEvent:
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


def fake_v11_group_exe_code(
    group_id: int, user_id: int, code: str | Message
) -> GroupMessageEvent:
    return fake_v11_group_message_event(
        group_id=group_id,
        user_id=user_id,
        message=MessageSegment.text("code ") + code,
    )


def fake_v11_private_exe_code(user_id: int, code: str | Message) -> PrivateMessageEvent:
    from nonebot.adapters.onebot.v11 import MessageSegment

    return fake_v11_private_message_event(
        user_id=user_id,
        message=MessageSegment.text("code ") + code,
    )


@overload
def fake_v11_event_session(
    bot: Bot,
) -> tuple[PrivateMessageEvent, "Session"]: ...
@overload
def fake_v11_event_session(
    bot: Bot, user_id: int
) -> tuple[PrivateMessageEvent, "Session"]: ...
@overload
def fake_v11_event_session(
    bot: Bot, *, group_id: int
) -> tuple[GroupMessageEvent, "Session"]: ...
@overload
def fake_v11_event_session(
    bot: Bot, user_id: int, group_id: int
) -> tuple[GroupMessageEvent, "Session"]: ...


def fake_v11_event_session(
    bot: Bot,
    user_id: int | None = None,
    group_id: int | None = None,
) -> tuple[GroupMessageEvent | PrivateMessageEvent, "Session"]:
    from nonebot_plugin_session import extract_session

    user_id = user_id or fake_user_id()
    message = Message()
    if group_id is not None:
        event = fake_v11_group_message_event(
            user_id=user_id,
            group_id=group_id,
            message=message,
        )
    else:
        event = fake_v11_private_message_event(
            user_id=user_id,
            message=message,
        )
    session = extract_session(bot, event)
    return event, session
