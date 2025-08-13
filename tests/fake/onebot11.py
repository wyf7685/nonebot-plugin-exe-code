# ruff: noqa: N806

import contextlib
from collections.abc import AsyncGenerator, Callable, Generator
from typing import TYPE_CHECKING, Any, Literal, overload

from nonebot.adapters.onebot.v11 import Adapter, Bot, Message, MessageSegment
from nonebot.adapters.onebot.v11.event import (
    GroupMessageEvent,
    PrivateMessageEvent,
    Sender,
)
from nonebug.mixin.call_api import ApiContext
from nonebug.mixin.process import MatcherContext
from pydantic import create_model

from .common import (
    ensure_context,
    fake_api,
    fake_bot,
    fake_message_id,
    fake_user_id,
    get_uninfo_fetcher,
)

if TYPE_CHECKING:
    from nonebot_plugin_exe_code.interface.adapters.onebot11 import API

type MessageEvent = GroupMessageEvent | PrivateMessageEvent


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
        message_id: int = fake_message_id()
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
        message_id: int = fake_message_id()
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
def fake_v11_event() -> PrivateMessageEvent: ...
@overload
def fake_v11_event(user_id: int) -> PrivateMessageEvent: ...
@overload
def fake_v11_event(*, group_id: int) -> GroupMessageEvent: ...
@overload
def fake_v11_event(user_id: int, group_id: int) -> GroupMessageEvent: ...
@overload
def fake_v11_event(
    *,
    user_id: int | None = None,
    group_id: int | None = None,
) -> MessageEvent: ...


def fake_v11_event(
    user_id: int | None = None,
    group_id: int | None = None,
) -> MessageEvent:
    user_id = user_id or fake_user_id()
    if group_id is not None:
        return fake_v11_group_message_event(
            user_id=user_id,
            group_id=group_id,
            message=Message(),
        )

    return fake_v11_private_message_event(
        user_id=user_id,
        message=Message(),
    )


def make_v11_session_cache(
    bot: Bot,
    event: MessageEvent,
) -> Callable[[], object]:
    fetcher = get_uninfo_fetcher(bot)

    data = fetcher.supply_self(bot) | {
        "user_id": str(event.user_id),
        "name": event.sender.nickname,
        "nickname": event.sender.card,
        "gender": event.sender.sex or "unknown",
    }
    if isinstance(event, GroupMessageEvent):
        data |= {
            "group_id": str(event.group_id),
            "group_name": "group_name",
            "card": "card",
            "role": event.sender.role,
            "join_time": 0,
        }

    session_id = fetcher.get_session_id(event)
    fetcher.session_cache[session_id] = fetcher.parse(data)
    return lambda: fetcher.session_cache.pop(session_id, None)


@contextlib.contextmanager
def ensure_v11_session_cache(
    bot: Bot,
    event: MessageEvent,
    *,
    do_cleanup: bool = True,
) -> Generator[Callable[[], object]]:
    cleanup = make_v11_session_cache(bot, event)
    try:
        yield cleanup
    finally:
        if do_cleanup:
            cleanup()


@contextlib.asynccontextmanager
async def ensure_v11_api(
    ctx: ApiContext,
    *,
    user_id: int | None = None,
    group_id: int | None = None,
) -> AsyncGenerator["API"]:
    bot = fake_v11_bot(ctx)
    event = fake_v11_event(user_id=user_id, group_id=group_id)
    with ensure_v11_session_cache(bot, event):
        api = await fake_api(bot, event)
        async with ensure_context(bot, event):
            try:
                yield api
            finally:
                ctx.connected_bot.discard(bot)
                bot.adapter.bot_disconnect(bot)
