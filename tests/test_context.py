import asyncio

import pytest
from nonebot.adapters.onebot.v11 import Adapter, Bot, Message
from nonebug import App

from tests.fake import ensure_context, fake_event_session, fake_user_id


@pytest.mark.asyncio()
async def test_lock(app: App):
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        adapter = ctx.create_adapter(base=Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        bot.adapter.__class__.get_name = Adapter.get_name

        event, session = fake_event_session(bot)

        async def _test(delay: float, code: str):
            await asyncio.sleep(delay)
            await Context.execute(bot, session, code)

        ctx.should_call_send(event, Message("1"))
        ctx.should_call_send(event, Message("2"))

        with ensure_context(bot, event):
            await asyncio.gather(
                _test(0, "print(1); await sleep(0.1)"),
                _test(0.01, "print(2)"),
            )


@pytest.mark.asyncio()
async def test_cancel(app: App):
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        adapter = ctx.create_adapter(base=Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        bot.adapter.__class__.get_name = Adapter.get_name

        event, session = fake_event_session(bot)
        result = False

        async def _test1():
            with pytest.raises(asyncio.CancelledError):
                await Context.execute(bot, session, "await sleep(1); print(1)")

        async def _test2():
            nonlocal result
            await asyncio.sleep(0.01)
            result = Context.get_context(session).cancel()

        with ensure_context(bot, event):
            await asyncio.gather(_test1(), _test2())
        assert result


def test_context_variable():
    from nonebot_plugin_alconna.uniseg import Image, UniMessage

    from nonebot_plugin_exe_code.context import Context

    context = Context.get_context(str(fake_user_id()))

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
