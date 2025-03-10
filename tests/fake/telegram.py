# ruff: noqa: N806, S106

from typing import TYPE_CHECKING, Any, Literal, overload

from nonebot.adapters.telegram import Adapter, Bot, Message
from nonebot.adapters.telegram.config import BotConfig
from nonebot.adapters.telegram.event import (
    GroupMessageEvent,
    MessageEvent,
    PrivateMessageEvent,
)
from nonebot.adapters.telegram.model import Chat, User
from nonebug.mixin.call_api import ApiContext
from nonebug.mixin.process import MatcherContext
from pydantic import create_model

from .common import fake_bot, fake_user_id

if TYPE_CHECKING:
    from nonebot_plugin_session import Session


def fake_telegram_bot(ctx: ApiContext | MatcherContext, **kwargs: Any) -> Bot:
    return fake_bot(
        ctx,
        Adapter,
        Bot,
        config=BotConfig(token="token"),
        **kwargs,
    )


def fake_telegram_private_message_event(**field: Any) -> PrivateMessageEvent:
    _Fake = create_model("_Fake", __base__=PrivateMessageEvent)
    user_id = field.pop("user_id", None) or 10

    class FakeEvent(_Fake):
        message_id: int = 1
        date: int = 1000000
        chat: Chat = Chat(id=10000, type="private")
        forward_from: User | None = None
        forward_from_chat: Chat | None = None
        forward_from_message_id: int | None = None
        forward_signature: str | None = None
        forward_sender_name: str | None = None
        forward_date: int | None = None
        via_bot: User | None = None
        has_protected_content: Literal[True] | None = None
        media_group_id: str | None = None
        author_signature: str | None = None
        reply_to_message: MessageEvent | None = None
        message: Message = Message()
        original_message: Message = Message()
        _tome: bool = False
        from_: User = User(id=user_id, is_bot=False, first_name="10")

    return FakeEvent(**field)


def fake_telegram_group_message_event(**field: Any) -> GroupMessageEvent:
    _Fake = create_model("_Fake", __base__=GroupMessageEvent)
    user_id = field.pop("user_id", 10)
    group_id = field.pop("group_id", 10000)

    class FakeEvent(_Fake):
        message_id: int = 1
        date: int = 1000000
        chat: Chat = Chat(id=group_id, type="group")
        forward_from: User | None = None
        forward_from_chat: Chat | None = None
        forward_from_message_id: int | None = None
        forward_signature: str | None = None
        forward_sender_name: str | None = None
        forward_date: int | None = None
        via_bot: User | None = None
        has_protected_content: Literal[True] | None = None
        media_group_id: str | None = None
        author_signature: str | None = None
        reply_to_message: MessageEvent | None = None
        message: Message = Message()
        original_message: Message = Message()
        _tome: bool = False
        from_: User = User(id=user_id, is_bot=False, first_name="10")
        sender_chat: Chat | None = None

    return FakeEvent(**field)


@overload
def fake_telegram_event_session(
    bot: Bot,
) -> tuple[PrivateMessageEvent, "Session"]: ...
@overload
def fake_telegram_event_session(
    bot: Bot, user_id: int
) -> tuple[PrivateMessageEvent, "Session"]: ...
@overload
def fake_telegram_event_session(
    bot: Bot, *, group_id: int
) -> tuple[GroupMessageEvent, "Session"]: ...
@overload
def fake_telegram_event_session(
    bot: Bot, user_id: int, group_id: int
) -> tuple[GroupMessageEvent, "Session"]: ...


def fake_telegram_event_session(
    bot: Bot,
    user_id: int | None = None,
    group_id: int | None = None,
) -> tuple[PrivateMessageEvent | GroupMessageEvent, "Session"]:
    from nonebot_plugin_session import extract_session

    user_id = user_id or fake_user_id()
    if group_id is not None:
        event = fake_telegram_private_message_event(
            user_id=user_id,
            group_id=group_id,
            message=Message(),
        )
    else:
        event = fake_telegram_group_message_event(
            user_id=user_id,
            message=Message(),
        )
    session = extract_session(bot, event)
    return event, session
