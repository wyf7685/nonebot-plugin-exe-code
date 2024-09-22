# ruff: noqa: ANN401, N806, S106

import contextlib
import itertools
from collections.abc import Callable, Generator
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal, TypeVar, overload

import nonebot
from nonebug.mixin.call_api import ApiContext
from nonebug.mixin.process import MatcherContext

if TYPE_CHECKING:
    from nonebot.adapters import Adapter, Bot, Event, console, qq, satori, telegram
    from nonebot.adapters.onebot import v11
    from nonebot.adapters.telegram import event as tgevent
    from nonebot.matcher import Matcher
    from nonebot_plugin_session import Session


def _faker(start: int) -> Callable[[], int]:
    gen = itertools.count(start)

    def faker() -> int:
        return next(gen)

    return faker


fake_user_id = _faker(100000)
fake_group_id = _faker(200000)
fake_img_bytes = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```"
    b"\x00\x00\x00\x04\x00\x01\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82"
)

B = TypeVar("B", bound="Bot")


def fake_bot(
    ctx: ApiContext | MatcherContext,
    adapter_base: type["Adapter"],
    bot_base: type[B],
    **kwargs: Any,
) -> B:
    return ctx.create_bot(
        base=bot_base,
        adapter=nonebot.get_adapter(adapter_base),
        **kwargs,
    )


def fake_v11_bot(ctx: ApiContext | MatcherContext, **kwargs: Any) -> "v11.Bot":
    from nonebot.adapters.onebot.v11 import Adapter, Bot

    return fake_bot(ctx, Adapter, Bot, **kwargs)


def fake_console_bot(ctx: ApiContext | MatcherContext, **kwargs: Any) -> "console.Bot":
    from nonebot.adapters.console import Adapter, Bot

    return fake_bot(ctx, Adapter, Bot, **kwargs)


def fake_qq_bot(ctx: ApiContext | MatcherContext, **kwargs: Any) -> "qq.Bot":
    from nonebot.adapters.qq import Adapter, Bot
    from nonebot.adapters.qq.config import BotInfo

    return fake_bot(
        ctx,
        Adapter,
        Bot,
        bot_info=BotInfo(
            id="app_id",
            token="app_token",
            secret="app_secret",
        ),
        **kwargs,
    )


def fake_satori_bot(ctx: ApiContext | MatcherContext, **kwargs: Any) -> "satori.Bot":
    from nonebot.adapters.satori import Adapter, Bot
    from nonebot.adapters.satori.config import ClientInfo
    from nonebot.adapters.satori.models import Login, LoginStatus

    return fake_bot(
        ctx,
        Adapter,
        Bot,
        login=Login(status=LoginStatus.ONLINE),
        info=ClientInfo(port=8080),
        **kwargs,
    )


def fake_telegram_bot(
    ctx: ApiContext | MatcherContext, **kwargs: Any
) -> "telegram.Bot":
    from nonebot.adapters.telegram import Adapter, Bot
    from nonebot.adapters.telegram.config import BotConfig

    return fake_bot(
        ctx,
        Adapter,
        Bot,
        config=BotConfig(token="token"),
        **kwargs,
    )


def fake_v11_group_message_event(**field: Any) -> "v11.GroupMessageEvent":
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


def fake_v11_private_message_event(**field: Any) -> "v11.PrivateMessageEvent":
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


def fake_console_message_event(**field: Any) -> "console.MessageEvent":
    from nonebot.adapters.console import Message, MessageEvent, User
    from pydantic import create_model

    _Fake = create_model("_Fake", __base__=MessageEvent)

    class FakeEvent(_Fake):
        time: datetime = datetime.now()  # noqa: DTZ005
        self_id: str = "pytest"
        post_type: Literal["message"] = "message"
        user: User = User("nonebug")
        message: Message = Message()

    return FakeEvent(**field)


def fake_qq_message_create_event(**field: Any) -> "qq.MessageCreateEvent":
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


def fake_qq_c2c_message_create_event(**field: Any) -> "qq.C2CMessageCreateEvent":
    from nonebot.adapters.qq import C2CMessageCreateEvent
    from nonebot.adapters.qq.models.qq import Attachment, FriendAuthor
    from pydantic import create_model

    _Fake = create_model("_Fake", __base__=C2CMessageCreateEvent)

    class FakeEvent(_Fake):
        id: str = "id"
        content: str = "test"
        timestamp: str = "1000000"
        attachments: list[Attachment] | None = None
        _reply_seq: int = -1
        author: FriendAuthor = FriendAuthor(id="id", user_openid="user_openid")
        to_me: bool = True

    return FakeEvent(**field)


def fake_satori_private_message_created_event(
    **field: Any,
) -> "satori.event.PrivateMessageCreatedEvent":
    from nonebot.adapters.satori.event import EventType, PrivateMessageCreatedEvent
    from nonebot.adapters.satori.message import RenderMessage
    from nonebot.adapters.satori.models import Channel, ChannelType, User
    from nonebot.adapters.satori.models import MessageObject as SatoriMessage
    from pydantic import create_model

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
        message: SatoriMessage = SatoriMessage(id="10000", content="")
        to_me: bool = False
        reply: RenderMessage | None = None

    return FakeEvent(**field)


def fake_satori_public_message_created_event(
    **field: Any,
) -> "satori.event.PublicMessageCreatedEvent":
    from nonebot.adapters.satori.event import EventType, PublicMessageCreatedEvent
    from nonebot.adapters.satori.message import RenderMessage
    from nonebot.adapters.satori.models import Channel, ChannelType, Member, User
    from nonebot.adapters.satori.models import MessageObject as SatoriMessage
    from pydantic import create_model

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
        message: SatoriMessage = SatoriMessage(id="10000", content="")
        to_me: bool = False
        reply: RenderMessage | None = None

    return FakeEvent(**field)


def fake_telegram_private_message_event(**field: Any) -> "tgevent.PrivateMessageEvent":
    from nonebot.adapters.telegram.event import MessageEvent, PrivateMessageEvent
    from nonebot.adapters.telegram.message import Message
    from nonebot.adapters.telegram.model import Chat, User
    from pydantic import create_model

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


def fake_telegram_group_message_event(**field: Any) -> "tgevent.GroupMessageEvent":
    from nonebot.adapters.telegram.event import GroupMessageEvent, MessageEvent
    from nonebot.adapters.telegram.message import Message
    from nonebot.adapters.telegram.model import Chat, User
    from pydantic import create_model

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


def fake_v11_group_exe_code(
    group_id: int, user_id: int, code: "str | v11.Message"
) -> "v11.GroupMessageEvent":
    from nonebot.adapters.onebot.v11 import MessageSegment

    return fake_v11_group_message_event(
        group_id=group_id,
        user_id=user_id,
        message=MessageSegment.text("code ") + code,
    )


def fake_v11_private_exe_code(
    user_id: int, code: "str | v11.Message"
) -> "v11.PrivateMessageEvent":
    from nonebot.adapters.onebot.v11 import MessageSegment

    return fake_v11_private_message_event(
        user_id=user_id,
        message=MessageSegment.text("code ") + code,
    )


def fake_qq_guild_exe_code(
    user_id: str, channel_id: str, guild_id: str, code: str
) -> "qq.MessageCreateEvent":
    from nonebot.adapters.qq.models.guild import User

    return fake_qq_message_create_event(
        channel_id=channel_id,
        guild_id=guild_id,
        user=User(id=user_id),
        content=f"code {code}",
    )


def fake_qq_c2c_exe_code(user_id: str, code: str) -> "qq.C2CMessageCreateEvent":
    from nonebot.adapters.qq.models.qq import FriendAuthor

    return fake_qq_c2c_message_create_event(
        content=f"code {code}",
        author=FriendAuthor(id=user_id, user_openid=user_id),
    )


def fake_satori_private_exe_code(
    user_id: str, code: "str | satori.Message"
) -> "satori.event.PrivateMessageCreatedEvent":
    from nonebot.adapters.satori import MessageSegment

    return fake_satori_private_message_created_event(
        user_id=user_id,
        content=MessageSegment.text("code ") + code,
    )


def fake_satori_public_exe_code(
    user_id: str, channel_id: str, code: "str | satori.Message"
) -> "satori.event.PublicMessageCreatedEvent":
    from nonebot.adapters.satori import MessageSegment

    return fake_satori_public_message_created_event(
        user_id=user_id,
        channel_id=channel_id,
        content=MessageSegment.text("code ") + code,
    )


@overload
def fake_v11_event_session(
    bot: "v11.Bot",
) -> tuple["v11.PrivateMessageEvent", "Session"]: ...
@overload
def fake_v11_event_session(
    bot: "v11.Bot", user_id: int
) -> tuple["v11.PrivateMessageEvent", "Session"]: ...
@overload
def fake_v11_event_session(
    bot: "v11.Bot", *, group_id: int
) -> tuple["v11.GroupMessageEvent", "Session"]: ...
@overload
def fake_v11_event_session(
    bot: "v11.Bot", user_id: int, group_id: int
) -> tuple["v11.GroupMessageEvent", "Session"]: ...


def fake_v11_event_session(
    bot: "v11.Bot",
    user_id: int | None = None,
    group_id: int | None = None,
) -> tuple["v11.GroupMessageEvent | v11.PrivateMessageEvent", "Session"]:
    from nonebot.adapters.onebot.v11 import Message
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


def fake_qq_event_session(
    bot: "qq.Bot",
    user_id: str | None = None,
    channel_id: str | None = None,
    guild_id: str | None = None,
) -> tuple["qq.MessageCreateEvent | qq.C2CMessageCreateEvent", "Session"]:
    from nonebot.adapters.qq.models.guild import User
    from nonebot.adapters.qq.models.qq import FriendAuthor
    from nonebot_plugin_session import extract_session

    user_id = user_id or str(fake_user_id())
    if channel_id is not None and guild_id is not None:
        event = fake_qq_message_create_event(
            channel_id=channel_id,
            guild_id=guild_id,
            user=User(id=user_id),
            content="",
        )
    else:
        event = fake_qq_c2c_message_create_event(
            content="",
            author=FriendAuthor(id=user_id, user_openid=user_id),
        )

    session = extract_session(bot, event)
    return event, session


@overload
def fake_satori_event_session(
    bot: "satori.Bot",
) -> tuple["satori.event.PrivateMessageCreatedEvent", "Session"]: ...
@overload
def fake_satori_event_session(
    bot: "satori.Bot", user_id: str
) -> tuple["satori.event.PrivateMessageCreatedEvent", "Session"]: ...
@overload
def fake_satori_event_session(
    bot: "satori.Bot", *, channel_id: str
) -> tuple["satori.event.PublicMessageCreatedEvent", "Session"]: ...
@overload
def fake_satori_event_session(
    bot: "satori.Bot", user_id: str, channel_id: str
) -> tuple["satori.event.PublicMessageCreatedEvent", "Session"]: ...


def fake_satori_event_session(
    bot: "satori.Bot",
    user_id: str | None = None,
    channel_id: str | None = None,
) -> tuple[
    "satori.event.PrivateMessageCreatedEvent | satori.event.PublicMessageCreatedEvent",
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


@contextlib.contextmanager
def ensure_context(
    bot: "Bot",
    event: "Event",
    matcher: "Matcher | None" = None,
) -> Generator[None, Any, None]:
    # ref: `nonebot.internal.matcher.matcher:Matcher.ensure_context`
    from nonebot.internal.matcher import current_bot, current_event, current_matcher

    b = current_bot.set(bot)
    e = current_event.set(event)
    m = current_matcher.set(matcher) if matcher else None

    try:
        yield
    finally:
        current_bot.reset(b)
        current_event.reset(e)
        if m:
            current_matcher.reset(m)
