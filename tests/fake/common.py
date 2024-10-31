import contextlib
import itertools
from collections.abc import Generator
from typing import Any

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


@contextlib.contextmanager
def ensure_context(
    bot: Bot,
    event: Event,
    matcher: Matcher | None = None,
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
