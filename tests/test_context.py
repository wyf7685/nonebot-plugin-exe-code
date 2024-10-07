# ruff: noqa: S101

import asyncio

import pytest
from nonebot.adapters.onebot.v11 import Message
from nonebug import App

from tests.fake import ensure_context, fake_v11_bot, fake_v11_event_session


@pytest.mark.asyncio
async def test_lock(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot)

        async def _test(delay: float, code: str) -> None:
            await asyncio.sleep(delay)
            await Context.execute(bot, event, code)

        ctx.should_call_send(event, Message("1"))
        ctx.should_call_send(event, Message("2"))

        with ensure_context(bot, event):
            await asyncio.gather(
                _test(0, "print(1); await sleep(0.1)"),
                _test(0.01, "print(2)"),
            )


@pytest.mark.asyncio
async def test_cancel(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, session = fake_v11_event_session(bot)
        result = False

        async def _test1() -> None:
            with pytest.raises(asyncio.CancelledError):
                await Context.execute(bot, event, "await sleep(1); print(1)")

        async def _test2() -> None:
            nonlocal result
            await asyncio.sleep(0.01)
            result = Context.get_context(session).cancel()

        with ensure_context(bot, event):
            await asyncio.gather(_test1(), _test2())
        assert result


@pytest.mark.asyncio
async def test_context_variable(app: App) -> None:
    from nonebot_plugin_alconna.uniseg import Image, UniMessage

    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        _, session = fake_v11_event_session(bot)
        context = Context.get_context(session)

    key, val = "aaa", 111
    context.set_value(key, val)
    assert context.ctx.get(key) == val
    context.set_value(key, None)
    assert key not in context.ctx

    key, val = "gurl", "http://localhost/image.png"
    unimsg = UniMessage.image(url=val)
    context.set_gurl(unimsg)
    assert context.ctx.pop(key) == val
    context.set_gurl(unimsg[Image, 0])
    assert context.ctx.pop(key) == val
    context.set_gurl(UniMessage())
    assert key not in context.ctx

    key, val = "abc", 123
    context[key] = val
    assert context[key] == val
    del context[key]
    assert key not in context.ctx


@pytest.mark.asyncio
async def test_session_fetch(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, session = fake_v11_event_session(bot)
        wrong_event, _ = fake_v11_event_session(bot)

        with (
            ensure_context(bot, wrong_event),
            pytest.raises(RuntimeError, match="event mismatch"),
        ):
            Context.get_context(event)

        with ensure_context(bot, event):
            with pytest.raises(RuntimeError, match="not initialized"):
                Context.get_context(event)
            with pytest.raises(RuntimeError, match="not initialized"):
                Context.get_context(event.get_user_id())

            Context.get_context(session)
            Context.get_context(event)
            Context.get_context(event.get_user_id())


@pytest.mark.asyncio
async def test_async_generator_executor(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.interface.utils import ReachLimit

    ReachLimit.limit = 3

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, session = fake_v11_event_session(bot)

        ctx.should_call_send(event, Message("1"))
        ctx.should_call_send(event, Message("2"))
        ctx.should_call_send(event, Message("3"))
        with ensure_context(bot, event), pytest.raises(ReachLimit):
            await Context.get_context(session).execute(
                bot, event, "yield 1\nyield 2\nyield 3\nyield 4"
            )
