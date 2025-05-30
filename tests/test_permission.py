import pytest
from nonebug import App

from .conftest import exe_code_group, exe_code_user, superuser
from .fake.common import fake_group_id, fake_user_id
from .fake.onebot11 import (
    fake_v11_bot,
    fake_v11_group_exe_code,
    fake_v11_private_exe_code,
    make_v11_session_cache,
)

fake_code = "a = 1"


@pytest.mark.asyncio
async def test_superuser_private(app: App) -> None:
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        bot = fake_v11_bot(ctx)
        event = fake_v11_private_exe_code(superuser, fake_code)
        cleanup = make_v11_session_cache(bot, event)
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_finished(matcher)
    cleanup()


@pytest.mark.asyncio
async def test_superuser_group(app: App) -> None:
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        bot = fake_v11_bot(ctx)
        group_id = fake_group_id()
        event = fake_v11_group_exe_code(group_id, superuser, fake_code)
        cleanup = make_v11_session_cache(bot, event)
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_finished(matcher)
    cleanup()


@pytest.mark.asyncio
async def test_exe_code_user_private(app: App) -> None:
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        bot = fake_v11_bot(ctx)
        event = fake_v11_private_exe_code(exe_code_user, fake_code)
        cleanup = make_v11_session_cache(bot, event)
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_finished(matcher)
    cleanup()


@pytest.mark.asyncio
async def test_exe_code_user_group(app: App) -> None:
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        bot = fake_v11_bot(ctx)
        group_id = fake_group_id()
        event = fake_v11_group_exe_code(group_id, exe_code_user, fake_code)
        cleanup = make_v11_session_cache(bot, event)
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_finished(matcher)
    cleanup()


@pytest.mark.asyncio
async def test_exe_code_group(app: App) -> None:
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        bot = fake_v11_bot(ctx)
        user_id = fake_user_id()
        event = fake_v11_group_exe_code(exe_code_group, user_id, fake_code)
        cleanup = make_v11_session_cache(bot, event)
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_finished(matcher)
    cleanup()


@pytest.mark.asyncio
async def test_not_allow_private(app: App) -> None:
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        bot = fake_v11_bot(ctx)
        user_id = fake_user_id()
        event = fake_v11_private_exe_code(user_id, fake_code)
        cleanup = make_v11_session_cache(bot, event)
        ctx.receive_event(bot, event)
        ctx.should_not_pass_permission(matcher)
    cleanup()


@pytest.mark.asyncio
async def test_not_allow_group(app: App) -> None:
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        bot = fake_v11_bot(ctx)
        user_id = fake_user_id()
        group_id = fake_group_id()
        event = fake_v11_group_exe_code(group_id, user_id, fake_code)
        cleanup = make_v11_session_cache(bot, event)
        ctx.receive_event(bot, event)
        ctx.should_not_pass_permission(matcher)
    cleanup()
