import contextlib
import itertools
from typing import TYPE_CHECKING, Any, overload

import nonebot
from nonebot.adapters import Adapter, Bot, Event
from nonebot.matcher import Matcher
from nonebug.mixin.call_api import ApiContext
from nonebug.mixin.dependent import DependentContext
from nonebug.mixin.process import MatcherContext

fake_user_id = (lambda: (g := itertools.count(100000)) and (lambda: next(g)))()
fake_group_id = (lambda: (g := itertools.count(200000)) and (lambda: next(g)))()
fake_img_bytes = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```"
    b"\x00\x00\x00\x04\x00\x01\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82"
)

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from nonebot.adapters import qq, satori, telegram
    from nonebot.adapters.onebot import v11 as onebot11
    from nonebot_plugin_uninfo.fetch import InfoFetcher
    from nonebot_plugin_user.models import UserSession

    from nonebot_plugin_exe_code.interface.adapters.onebot11 import API as V11API
    from nonebot_plugin_exe_code.interface.adapters.qq import API as QQAPI
    from nonebot_plugin_exe_code.interface.adapters.satori import API as SatoriAPI
    from nonebot_plugin_exe_code.interface.adapters.telegram import API as TelegramAPI
    from nonebot_plugin_exe_code.interface.api import API

    @overload
    async def fake_api(bot: onebot11.Bot, event: onebot11.Event) -> V11API: ...
    @overload
    async def fake_api(bot: qq.Bot, event: qq.Event) -> QQAPI: ...
    @overload
    async def fake_api(bot: satori.Bot, event: satori.event.Event) -> SatoriAPI: ...
    @overload
    async def fake_api(bot: telegram.Bot, event: telegram.Event) -> TelegramAPI: ...
    @overload
    async def fake_api[B: Bot, E: Event](bot: B, event: E) -> API[B, E]: ...

    @overload
    @contextlib.asynccontextmanager
    def ensure_context(
        bot: onebot11.Bot,
        event: onebot11.Event,
        matcher: Matcher | None = None,
    ) -> AsyncGenerator[V11API]: ...
    @overload
    @contextlib.asynccontextmanager
    def ensure_context(
        bot: qq.Bot,
        event: qq.Event,
        matcher: Matcher | None = None,
    ) -> AsyncGenerator[QQAPI]: ...
    @overload
    @contextlib.asynccontextmanager
    def ensure_context(
        bot: satori.Bot,
        event: satori.event.Event,
        matcher: Matcher | None = None,
    ) -> AsyncGenerator[SatoriAPI]: ...
    @overload
    @contextlib.asynccontextmanager
    def ensure_context(
        bot: telegram.Bot,
        event: telegram.Event,
        matcher: Matcher | None = None,
    ) -> AsyncGenerator[TelegramAPI]: ...
    @overload
    @contextlib.asynccontextmanager
    def ensure_context[B: Bot, E: Event](
        bot: B,
        event: E,
        matcher: Matcher | None = None,
    ) -> AsyncGenerator[API[B, E]]: ...


async def fake_session(bot: Bot, event: Event) -> "UserSession":
    from nonebot_plugin_uninfo import get_session
    from nonebot_plugin_user.params import get_user_session

    session = await get_user_session(await get_session(bot, event))
    assert session is not None, "Session is None"
    return session


async def fake_api(bot: Bot, event: Event) -> "API":
    from nonebot_plugin_exe_code.interface import create_api, get_default_context

    session = await fake_session(bot, event)
    return await create_api(bot, event, get_default_context(), session)


@contextlib.asynccontextmanager
async def ensure_context(
    bot: Bot,
    event: Event,
    matcher: Matcher | None = None,
) -> "AsyncGenerator[API]":
    # ref: `nonebot.internal.matcher.matcher:Matcher.ensure_context`
    from nonebot.internal.matcher import current_bot, current_event, current_matcher

    b = current_bot.set(bot)
    e = current_event.set(event)
    m = current_matcher.set(matcher) if matcher else None

    try:
        yield await fake_api(bot, event)
    finally:
        current_bot.reset(b)
        current_event.reset(e)
        if m:
            current_matcher.reset(m)


def fake_bot[B: Bot](
    ctx: ApiContext | MatcherContext | DependentContext,
    adapter_base: type[Adapter],
    bot_base: type[B],
    **kwargs: Any,
) -> B:
    return ctx.create_bot(
        base=bot_base,
        adapter=nonebot.get_adapter(adapter_base),
        **kwargs,
    )


def get_uninfo_fetcher(bot: Bot) -> "InfoFetcher":
    from nonebot_plugin_uninfo.adapters import INFO_FETCHER_MAPPING, alter_get_fetcher

    adapter = bot.adapter.get_name()
    fetcher = INFO_FETCHER_MAPPING.get(adapter) or alter_get_fetcher(adapter)
    assert fetcher is not None, "fetcher is None"
    return fetcher
