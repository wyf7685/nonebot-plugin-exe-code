import asyncio

import pytest
from nonebot.exception import FinishedException
from nonebot.adapters.onebot.v11 import Adapter, Bot, Message, MessageSegment
from nonebot.adapters.onebot.v11.event import Reply, Sender
from nonebug import App

from tests.conftest import exe_code_group, superuser
from tests.fake import (
    ensure_context,
    fake_bot,
    fake_img_bytes,
    fake_user_id,
    fake_v11_event_session,
    fake_v11_group_message_event,
)


@pytest.mark.asyncio()
async def test_getraw(app: App):
    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.matchers.getraw import matcher

    async with app.test_matcher(matcher) as ctx:
        bot = fake_bot(ctx, Adapter, Bot)
        reply_msg = MessageSegment.reply(123) + MessageSegment.at(456) + "789"
        event = fake_v11_group_message_event(
            message=Message(MessageSegment.text("getraw")),
            user_id=superuser,
            reply=Reply(
                time=1000000,
                message_type="test",
                message_id=1,
                real_id=1,
                sender=Sender(
                    card="",
                    nickname="test",
                    role="member",
                ),
                message=reply_msg,
            ),
        )
        expected = Message(MessageSegment.text(str(reply_msg)))

        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_send(event, expected)
        ctx.should_finished(matcher)

    context = Context.get_context(str(superuser)).ctx
    gem = context.get("gem")
    assert gem is not None, "Context variable `gem` not set"
    assert (
        gem == reply_msg
    ), f"Context variable `gem` error: expect `{reply_msg}`, got `{gem}`"

    gurl = context.get("gurl")
    assert gurl is None, "Got unexpected variable `gurl`"


@pytest.mark.asyncio()
async def test_getmid(app: App):
    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.matchers.getmid import matcher

    async with app.test_matcher(matcher) as ctx:
        bot = fake_bot(ctx, Adapter, Bot)
        reply_msg = MessageSegment.reply(123) + MessageSegment.at(456) + "789"
        event = fake_v11_group_message_event(
            message=Message(MessageSegment.text("getmid")),
            user_id=superuser,
            reply=Reply(
                time=1000000,
                message_type="test",
                message_id=1,
                real_id=1,
                sender=Sender(
                    card="",
                    nickname="test",
                    role="member",
                ),
                message=reply_msg,
            ),
        )
        expected = Message("1")

        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_send(event, expected)
        ctx.should_finished(matcher)

    context = Context.get_context(str(superuser)).ctx
    gem = context.get("gem")
    assert gem is not None, "Context variable `gem` not set"
    assert (
        gem == reply_msg
    ), f"Context variable `gem` error: expect `{reply_msg}`, got `{gem}`"

    gurl = context.get("gurl")
    assert gurl is None, "Got unexpected variable `gurl`"


@pytest.mark.asyncio()
async def test_getimg(app: App):
    import PIL.Image

    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.matchers import getimg
    from nonebot_plugin_exe_code.matchers.getimg import matcher

    _image_fetch = getimg.image_fetch

    async def image_fetch(*_):
        return fake_img_bytes

    getimg.image_fetch = image_fetch

    async def _test(varname: str | None = None):
        async with app.test_matcher(matcher) as ctx:
            bot = fake_bot(ctx, Adapter, Bot)
            reply_msg = "some" + MessageSegment.image(file=fake_img_bytes) + "text"
            msg = MessageSegment.reply(1) + "getimg"
            if varname is not None:
                msg += f" {varname}"
                msg.reduce()
            else:
                varname = "img"
            event = fake_v11_group_message_event(
                message=msg,
                user_id=superuser,
                reply=Reply(
                    time=1000000,
                    message_type="test",
                    message_id=1,
                    real_id=1,
                    sender=Sender(
                        card="",
                        nickname="test",
                        role="member",
                    ),
                    message=reply_msg,
                ),
            )

            ctx.receive_event(bot, event)
            ctx.should_pass_permission(matcher)
            if varname.isidentifier():
                expected = Message(f"图片已保存至变量 {varname}")
            else:
                expected = Message(f"{varname} 不是一个合法的 Python 标识符")
            ctx.should_call_send(event, expected)
            ctx.should_finished(matcher)

        if varname.isidentifier():
            img = Context.get_context(event).ctx.get(varname)
            assert img is not None, f"Context variable `{varname}` not set for getimg"
            assert isinstance(img, PIL.Image.Image), (
                f"Context variable `{varname}` error: "
                f"expect `PIL.Image.Image`, got `{type(img)}`"
            )

    await _test()
    await _test("im")
    await _test("inva/id")

    getimg.image_fetch = _image_fetch


code_test_terminate = """\
await feedback("test 1")
await sleep(1)
await feedback("test 2")
"""


@pytest.mark.asyncio()
async def test_terminate(app: App):
    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.matchers.terminate import handle_terminate, matcher

    async with app.test_matcher(matcher) as ctx:
        bot = fake_bot(ctx, Adapter, Bot)
        event = fake_v11_group_message_event(
            group_id=exe_code_group,
            user_id=superuser,
            message=Message("terminate"),
        )
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_finished(matcher)

    async with app.test_api() as ctx:
        bot = fake_bot(ctx, Adapter, Bot)
        user_id = fake_user_id()
        event, session = fake_v11_event_session(bot, user_id)
        ctx.should_call_send(event, Message("test 1"))
        expected = "中止" + MessageSegment.at(user_id) + "的执行任务"
        ctx.should_call_send(event, expected)

        async def _test1():
            with pytest.raises(asyncio.CancelledError):
                await Context.execute(bot, session, code_test_terminate)

        async def _test2():
            await asyncio.sleep(0.05)
            with pytest.raises(FinishedException):
                await handle_terminate(target=str(user_id))

        with ensure_context(bot, event):
            await asyncio.gather(_test1(), _test2())
