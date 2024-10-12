# ruff: noqa: N806

from datetime import datetime
from typing import TYPE_CHECKING, Any, overload

from nonebot.adapters.satori import (
    Adapter,
    Bot,
    Message,
    MessageSegment,
)
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
    LoginStatus,
    Member,
    MessageObject,
    User,
)
from nonebug.mixin.call_api import ApiContext
from nonebug.mixin.process import MatcherContext
from pydantic import create_model

from .common import fake_bot, fake_user_id

if TYPE_CHECKING:
    from nonebot_plugin_session import Session


def fake_satori_bot(ctx: ApiContext | MatcherContext, **kwargs: Any) -> Bot:
    return fake_bot(
        ctx,
        Adapter,
        Bot,
        login=Login(status=LoginStatus.ONLINE),
        info=ClientInfo(port=8080),
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
def fake_satori_event_session(
    bot: Bot,
) -> tuple[PrivateMessageCreatedEvent, "Session"]: ...
@overload
def fake_satori_event_session(
    bot: Bot, user_id: str
) -> tuple[PrivateMessageCreatedEvent, "Session"]: ...
@overload
def fake_satori_event_session(
    bot: Bot, *, channel_id: str
) -> tuple[PublicMessageCreatedEvent, "Session"]: ...
@overload
def fake_satori_event_session(
    bot: Bot, user_id: str, channel_id: str
) -> tuple[PublicMessageCreatedEvent, "Session"]: ...


def fake_satori_event_session(
    bot: Bot,
    user_id: str | None = None,
    channel_id: str | None = None,
) -> tuple[
    PrivateMessageCreatedEvent | PublicMessageCreatedEvent,
    "Session",
]:
    from nonebot_plugin_session import extract_session

    user_id = str(user_id or fake_user_id())
    if channel_id is not None:
        event = fake_satori_public_message_created_event(
            user_id=user_id,
            channel_id=channel_id,
            content="",
        )
    else:
        event = fake_satori_private_message_created_event(
            user_id=user_id,
            content="",
        )
    session = extract_session(bot, event)
    return event, session
