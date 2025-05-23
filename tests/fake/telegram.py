# ruff: noqa: N806, S106

import contextlib
from collections.abc import AsyncGenerator, Callable, Generator
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

from .common import ensure_context, fake_api, fake_bot, fake_user_id, get_uninfo_fetcher

if TYPE_CHECKING:
    from nonebot_plugin_exe_code.interface.adapters.telegram import API


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
def fake_telegram_event() -> PrivateMessageEvent: ...
@overload
def fake_telegram_event(user_id: int) -> PrivateMessageEvent: ...
@overload
def fake_telegram_event(*, group_id: int) -> GroupMessageEvent: ...
@overload
def fake_telegram_event(user_id: int, group_id: int) -> GroupMessageEvent: ...
@overload
def fake_telegram_event(
    user_id: int | None, group_id: int | None
) -> PrivateMessageEvent | GroupMessageEvent: ...


def fake_telegram_event(
    user_id: int | None = None,
    group_id: int | None = None,
) -> PrivateMessageEvent | GroupMessageEvent:
    user_id = user_id or fake_user_id()
    if group_id is not None:
        return fake_telegram_private_message_event(
            user_id=user_id,
            group_id=group_id,
            message=Message(),
        )
    return fake_telegram_group_message_event(
        user_id=user_id,
        message=Message(),
    )


def make_telegram_session_cache(
    bot: Bot,
    event: PrivateMessageEvent | GroupMessageEvent,
) -> Callable[[], object]:
    fetcher = get_uninfo_fetcher(bot)

    user = event.from_
    data = fetcher.supply_self(bot) | {
        "user_id": str(user.id),
        "name": user.username or "",
        "nickname": user.first_name + (f" {user.last_name}" if user.last_name else ""),
        "avatar": None,
    }
    if isinstance(event, GroupMessageEvent):
        data |= {
            "chat_id": str(event.chat.id),
            "chat_name": event.chat.title,
        }

    session_id = fetcher.get_session_id(event)
    fetcher.session_cache[session_id] = fetcher.parse(data)
    return lambda: fetcher.session_cache.pop(session_id, None)


@contextlib.contextmanager
def ensure_telegram_session_cache(
    bot: Bot,
    event: PrivateMessageEvent | GroupMessageEvent,
    *,
    do_cleanup: bool = True,
) -> Generator[Callable[[], object]]:
    cleanup = make_telegram_session_cache(bot, event)
    try:
        yield cleanup
    finally:
        if do_cleanup:
            cleanup()


@contextlib.asynccontextmanager
async def ensure_telegram_api(
    ctx: ApiContext,
    *,
    user_id: int | None = None,
    group_id: int | None = None,
) -> AsyncGenerator["API"]:
    bot = fake_telegram_bot(ctx)
    event = fake_telegram_event(user_id=user_id, group_id=group_id)

    with ensure_telegram_session_cache(bot, event):
        api = await fake_api(bot, event)
        async with ensure_context(bot, event):
            try:
                yield api
            finally:
                ctx.connected_bot.discard(bot)
                bot.adapter.bot_disconnect(bot)
