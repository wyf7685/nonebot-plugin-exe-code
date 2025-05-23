# ruff: noqa: N806, S106

import contextlib
from collections.abc import AsyncGenerator, Callable, Generator
from datetime import datetime
from typing import TYPE_CHECKING, Any

from nonebot.adapters.qq import Adapter, Bot, C2CMessageCreateEvent, MessageCreateEvent
from nonebot.adapters.qq.config import BotInfo
from nonebot.adapters.qq.models.common import (
    MessageArk,
    MessageAttachment,
    MessageEmbed,
    MessageReference,
)
from nonebot.adapters.qq.models.guild import Member, User
from nonebot.adapters.qq.models.qq import Attachment, FriendAuthor
from nonebug.mixin.call_api import ApiContext
from nonebug.mixin.process import MatcherContext
from pydantic import create_model

from .common import ensure_context, fake_api, fake_bot, fake_user_id, get_uninfo_fetcher

if TYPE_CHECKING:
    from nonebot_plugin_exe_code.interface.adapters.qq import API


type MessageEvent = MessageCreateEvent | C2CMessageCreateEvent


def fake_qq_bot(ctx: ApiContext | MatcherContext, **kwargs: Any) -> Bot:
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


def fake_qq_message_create_event(**field: Any) -> MessageCreateEvent:
    _Fake = create_model("_Fake", __base__=MessageCreateEvent)

    class FakeEvent(_Fake):
        id: str = "id"
        event_id: str | None = "event_id"
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


def fake_qq_c2c_message_create_event(**field: Any) -> C2CMessageCreateEvent:
    _Fake = create_model("_Fake", __base__=C2CMessageCreateEvent)

    class FakeEvent(_Fake):
        id: str = "id"
        event_id: str | None = "event_id"
        content: str = "test"
        timestamp: str = "1000000"
        attachments: list[Attachment] | None = None
        _reply_seq: int = -1
        author: FriendAuthor = FriendAuthor(id="id", user_openid="user_openid")
        to_me: bool = True

    return FakeEvent(**field)


def fake_qq_guild_exe_code(
    user_id: str, channel_id: str, guild_id: str, code: str
) -> MessageCreateEvent:
    from nonebot.adapters.qq.models.guild import User

    return fake_qq_message_create_event(
        channel_id=channel_id,
        guild_id=guild_id,
        user=User(id=user_id),
        content=f"code {code}",
    )


def fake_qq_c2c_exe_code(user_id: str, code: str) -> C2CMessageCreateEvent:
    return fake_qq_c2c_message_create_event(
        content=f"code {code}",
        author=FriendAuthor(id=user_id, user_openid=user_id),
    )


def fake_qq_event(
    user_id: str | None = None,
    channel_id: str | None = None,
    guild_id: str | None = None,
) -> MessageEvent:
    from nonebot.adapters.qq.models.guild import User
    from nonebot.adapters.qq.models.qq import FriendAuthor

    user_id = user_id or str(fake_user_id())
    if channel_id is not None and guild_id is not None:
        return fake_qq_message_create_event(
            channel_id=channel_id,
            guild_id=guild_id,
            user=User(id=user_id),
            content="",
        )
    return fake_qq_c2c_message_create_event(
        content="",
        author=FriendAuthor(id=user_id, user_openid=user_id),
    )


def make_qq_session_cache(
    bot: Bot,
    event: MessageEvent,
) -> Callable[[], object]:
    from nonebot_plugin_uninfo.model import Role

    fetcher = get_uninfo_fetcher(bot)
    data = fetcher.supply_self(bot)

    if isinstance(event, C2CMessageCreateEvent):
        data |= {
            "user_id": event.author.user_openid,
            "name": "",
            "nickname": "",
            "avatar": f"https://q.qlogo.cn/qqapp/{bot.bot_info.id}/{event.author.user_openid}/100",
        }
    elif isinstance(event, MessageCreateEvent):
        data |= {
            "user_id": event.author.id,
            "name": event.author.username or "",
            "nickname": "",
            "avatar": event.author.avatar,
            "guild_id": event.guild_id,
            "channel_id": event.channel_id,
        }

        if event.member:
            data |= {
                "nickname": event.member.nick or "",
                "role": Role("MEMBER", 1, "成员"),
                "joined_at": event.member.joined_at,
            }

    session = fetcher.parse(data)
    session_id = fetcher.get_session_id(event)
    fetcher.session_cache[session_id] = session
    return lambda: fetcher.session_cache.pop(session_id, None)


@contextlib.contextmanager
def ensure_qq_session_cache(
    bot: Bot,
    event: MessageEvent,
    *,
    do_cleanup: bool = True,
) -> Generator[Callable[[], object]]:
    cleanup = make_qq_session_cache(bot, event)
    try:
        yield cleanup
    finally:
        if do_cleanup:
            cleanup()


@contextlib.asynccontextmanager
async def ensure_qq_api(
    ctx: ApiContext,
    *,
    user_id: str | None = None,
    channel_id: str | None = None,
    guild_id: str | None = None,
) -> AsyncGenerator["API"]:
    bot = fake_qq_bot(ctx)
    event = fake_qq_event(
        user_id=user_id,
        channel_id=channel_id,
        guild_id=guild_id,
    )

    with ensure_qq_session_cache(bot, event):
        api = await fake_api(bot, event)
        async with ensure_context(bot, event):
            try:
                yield api
            finally:
                ctx.connected_bot.discard(bot)
                bot.adapter.bot_disconnect(bot)
