# ruff: noqa: S101

import pytest
from nonebot.adapters.qq import Message
from nonebug import App

from .conftest import exe_code_group
from .fake.common import ensure_context, fake_user_id
from .fake.qq import fake_qq_bot, fake_qq_event_session, fake_qq_guild_exe_code


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
        ctx.receive_event(bot, event)
        ctx.should_pass_permission()
        ctx.should_call_send(event, Message("123"))
        ctx.should_finished(matcher)


@pytest.mark.asyncio
async def test_qq_mid(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_qq_bot(ctx)
        event, _ = fake_qq_event_session(bot)
        ctx.should_call_send(event, Message("id"))
        with ensure_context(bot, event):
            await Context.execute(bot, event, "print(api.mid)")
