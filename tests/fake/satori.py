# ruff: noqa: N806

import contextlib
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import TYPE_CHECKING, Any, overload

from nonebot.adapters.satori import Adapter, Bot, Message, MessageSegment
from nonebot.adapters.satori.config import ClientInfo
from nonebot.adapters.satori.event import (
    EventType,
    PrivateMessageCreatedEvent,
    PublicMessageCreatedEvent,
)
from nonebot.adapters.satori.message import RenderMessage
from nonebot.adapters.satori.models import (
    Channel,
    ChannelType,
    Login,
    LoginOnline,
    LoginStatus,
    Member,
    MessageObject,
    User,
)
from nonebug.mixin.call_api import ApiContext
from nonebug.mixin.process import MatcherContext
from pydantic import create_model

from .common import ensure_context, fake_api, fake_bot, fake_user_id

if TYPE_CHECKING:
    from nonebot_plugin_exe_code.interface.adapters.satori import API


type MessageEvent = PrivateMessageCreatedEvent | PublicMessageCreatedEvent


def fake_satori_login() -> Login:
    return Login(
        sn=0,
        status=LoginStatus.ONLINE,
        adapter="satori",
        platform="platform",
    )


def fake_satori_bot(ctx: ApiContext | MatcherContext, **kwargs: Any) -> Bot:
    return fake_bot(
        ctx,
        Adapter,
        Bot,
        login=fake_satori_login(),
        info=ClientInfo(port=8080),
        proxy_urls=[],
        **kwargs,
    )


def fake_satori_private_message_created_event(
    **field: Any,
) -> PrivateMessageCreatedEvent:
    _Fake = create_model("_Fake", __base__=PrivateMessageCreatedEvent)
    user_id = field.pop("user_id", "10")
    field["message"] = {"id": "10000", "content": field.pop("content", "")}

    class FakeEvent(_Fake):
        __type__ = EventType.MESSAGE_CREATED
        id: int = 10000
        type: str = "message"
        platform: str = "fake"
        self_id: str = "100"
        timestamp: datetime = datetime.now()  # noqa: DTZ005
        login: LoginOnline = LoginOnline(
            sn=0,
            adapter="satori",
            platform="platform",
            user=User(id="100"),
        )
        channel: Channel = Channel(id=f"private:{user_id}", type=ChannelType.TEXT)
        user: User = User(id=user_id)
        message: MessageObject = MessageObject(id="10000", content="")
        to_me: bool = False
        reply: RenderMessage | None = None

    return FakeEvent(**field)


def fake_satori_public_message_created_event(
    **field: Any,
) -> PublicMessageCreatedEvent:
    _Fake = create_model("_Fake", __base__=PublicMessageCreatedEvent)
    user_id = field.pop("user_id", "10")
    channel_id = field.pop("channel_id", "100")
    field["message"] = {"id": "10000", "content": field.pop("content", "")}

    class FakeEvent(_Fake):
        __type__ = EventType.MESSAGE_CREATED
        id: int = 10000
        type: str = "message"
        platform: str = "fake"
        self_id: str = "100"
        timestamp: datetime = datetime.now()  # noqa: DTZ005
        login: LoginOnline = LoginOnline(
            sn=0,
            adapter="satori",
            platform="platform",
            user=User(id="100"),
        )
        channel: Channel = Channel(id=channel_id, type=ChannelType.TEXT)
        user: User = User(id=user_id)
        member: Member = Member(user=User(id=user_id))
        message: MessageObject = MessageObject(id="10000", content="")
        to_me: bool = False
        reply: RenderMessage | None = None

    return FakeEvent(**field)


def fake_satori_private_exe_code(
    user_id: str, code: str | Message
) -> PrivateMessageCreatedEvent:
    return fake_satori_private_message_created_event(
        user_id=user_id,
        content=MessageSegment.text("code ") + code,
    )


def fake_satori_public_exe_code(
    user_id: str, channel_id: str, code: str | Message
) -> PublicMessageCreatedEvent:
    return fake_satori_public_message_created_event(
        user_id=user_id,
        channel_id=channel_id,
        content=MessageSegment.text("code ") + code,
    )


@overload
def fake_satori_event() -> PrivateMessageCreatedEvent: ...
@overload
def fake_satori_event(user_id: str) -> PrivateMessageCreatedEvent: ...
@overload
def fake_satori_event(*, channel_id: str) -> PublicMessageCreatedEvent: ...
@overload
def fake_satori_event(user_id: str, channel_id: str) -> PublicMessageCreatedEvent: ...
@overload
def fake_satori_event(user_id: str | None, channel_id: str | None) -> MessageEvent: ...


def fake_satori_event(
    user_id: str | None = None,
    channel_id: str | None = None,
) -> MessageEvent:
    user_id = str(user_id or fake_user_id())
    if channel_id is not None:
        return fake_satori_public_message_created_event(
            user_id=user_id,
            channel_id=channel_id,
            content="",
        )
    return fake_satori_private_message_created_event(
        user_id=user_id,
        content="",
    )


@contextlib.asynccontextmanager
async def ensure_satori_api(
    ctx: ApiContext,
    *,
    user_id: str | None = None,
    channel_id: str | None = None,
) -> AsyncGenerator["API"]:
    bot = fake_satori_bot(ctx)
    event = fake_satori_event(user_id=user_id, channel_id=channel_id)
    api = await fake_api(bot, event)

    try:
        async with ensure_context(bot, event):
            yield api
    finally:
        ctx.connected_bot.discard(bot)
        bot.adapter.bot_disconnect(bot)
