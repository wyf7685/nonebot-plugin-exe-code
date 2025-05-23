# ruff: noqa: S101

import pytest
from nonebot.adapters.qq import Message
from nonebug import App

from .conftest import exe_code_group
from .fake.common import fake_user_id
from .fake.qq import (
    ensure_qq_api,
    fake_qq_bot,
    fake_qq_guild_exe_code,
    make_qq_session_cache,
)


@pytest.mark.asyncio
async def test_qq(app: App) -> None:
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        bot = fake_qq_bot(ctx)
        user_id = str(fake_user_id())
        event = fake_qq_guild_exe_code(
            user_id,
            str(exe_code_group),
            "test",
            "print(123)",
        )
        cleanup = make_qq_session_cache(bot, event)
        ctx.receive_event(bot, event)
        ctx.should_pass_permission()
        ctx.should_call_send(event, Message("123"))
        ctx.should_finished(matcher)
    cleanup()


@pytest.mark.asyncio
async def test_qq_mid(app: App) -> None:
    async with app.test_api() as ctx, ensure_qq_api(ctx) as api:
        assert api.mid == api.event.event_id
