import asyncio

import pytest
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot.adapters.onebot.v11.event import Reply, Sender
from nonebot.exception import FinishedException
from nonebug import App

from .conftest import exe_code_group, superuser
from .fake.common import ensure_context, fake_img_bytes, fake_session, fake_user_id
from .fake.onebot11 import (
    ensure_v11_session_cache,
    fake_v11_bot,
    fake_v11_event,
    fake_v11_group_message_event,
    make_v11_session_cache,
)


@pytest.mark.asyncio
async def test_getraw(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.matchers.getraw import matcher

    async with app.test_matcher(matcher) as ctx:
        bot = fake_v11_bot(ctx)
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
        cleanup = make_v11_session_cache(bot, event)
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_send(event, expected)
        ctx.should_finished(matcher)
    cleanup()

    async with app.test_matcher(matcher) as ctx:
        bot = fake_v11_bot(ctx)
        event = fake_v11_event(superuser)
        with ensure_v11_session_cache(bot, event):
            session = await fake_session(bot, event)
            context = Context.get_context(session).ctx
            gem = context.get("gem")
            assert gem is not None, "Context variable `gem` not set"
            assert gem == reply_msg, (
                f"Context variable `gem` error: expect `{reply_msg}`, got `{gem}`"
            )

            gurl = context.get("gurl")
            assert gurl is None, "Got unexpected variable `gurl`"


@pytest.mark.asyncio
async def test_getmid(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.matchers.getmid import matcher

    async with app.test_matcher(matcher) as ctx:
        bot = fake_v11_bot(ctx)
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

        cleanup = make_v11_session_cache(bot, event)
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_send(event, expected)
        ctx.should_finished(matcher)

    cleanup()

    async with app.test_matcher(matcher) as ctx:
        bot = fake_v11_bot(ctx)
        event = fake_v11_event(superuser)
        with ensure_v11_session_cache(bot, event):
            session = await fake_session(bot, event)
            context = Context.get_context(session).ctx
            gem = context.get("gem")
            assert gem is not None, "Context variable `gem` not set"
            assert gem == reply_msg, (
                f"Context variable `gem` error: expect `{reply_msg}`, got `{gem}`"
            )

            gurl = context.get("gurl")
            assert gurl is None, "Got unexpected variable `gurl`"


@pytest.mark.asyncio
async def test_getimg(app: App) -> None:
    # sourcery skip: use-fstring-for-concatenation
    import PIL.Image

    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.matchers import getimg
    from nonebot_plugin_exe_code.matchers.getimg import matcher

    _image_fetch = getimg.image_fetch

    async def image_fetch(*_: object) -> bytes:
        return fake_img_bytes

    getimg.image_fetch = image_fetch

    async def _test(varname: str | None = None) -> None:
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

        async with app.test_matcher(matcher) as ctx:
            bot = fake_v11_bot(ctx)
            cleanup = make_v11_session_cache(bot, event)
            ctx.receive_event(bot, event)
            ctx.should_pass_permission(matcher)
            if varname.isidentifier():
                expected = Message(f"图片已保存至变量 {varname}")
            else:
                expected = Message(f"{varname} 不是一个合法的 Python 标识符")
            ctx.should_call_send(event, expected)
            ctx.should_finished(matcher)

        cleanup()

        if varname.isidentifier():
            event = fake_v11_event(event.user_id)
            with ensure_v11_session_cache(bot, event):
                session = await fake_session(bot, event)

            img = Context.get_context(session).ctx.get(varname)
            assert img is not None, f"Context variable `{varname}` not set for getimg"
            assert isinstance(img, PIL.Image.Image), (
                f"Context variable `{varname}` error: "
                f"expect `PIL.Image.Image`, got `{type(img)}`"
            )

    await _test()
    await _test("im")
    await _test("inva/id")

    getimg.image_fetch = _image_fetch


@pytest.mark.asyncio
async def test_getimg_exception_1(app: App) -> None:
    # sourcery skip: use-fstring-for-concatenation
    from nonebot_plugin_exe_code.matchers import getimg
    from nonebot_plugin_exe_code.matchers.getimg import matcher

    _image_fetch = getimg.image_fetch

    async def image_fetch(*_: object) -> bytes:
        raise RuntimeError("test")

    getimg.image_fetch = image_fetch

    reply_msg = "some" + MessageSegment.image(file=fake_img_bytes) + "text"
    msg = MessageSegment.reply(1) + "getimg"
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
    expected = Message("保存图片时出错: test")

    async with app.test_matcher(matcher) as ctx:
        bot = fake_v11_bot(ctx)
        cleanup = make_v11_session_cache(bot, event)
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_send(event, expected)
        ctx.should_finished(matcher)

    cleanup()
    getimg.image_fetch = _image_fetch


@pytest.mark.asyncio
async def test_getimg_exception_2(app: App) -> None:
    # sourcery skip: use-fstring-for-concatenation
    from nonebot_plugin_exe_code.matchers import getimg
    from nonebot_plugin_exe_code.matchers.getimg import matcher

    _image_fetch = getimg.image_fetch

    async def image_fetch(*_: object) -> None:
        return None

    getimg.image_fetch = image_fetch

    reply_msg = "some" + MessageSegment.image(file=fake_img_bytes) + "text"
    msg = MessageSegment.reply(1) + "getimg"
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
    expected = Message("获取图片数据类型错误: <class 'NoneType'>")

    async with app.test_matcher(matcher) as ctx:
        bot = fake_v11_bot(ctx)
        cleanup = make_v11_session_cache(bot, event)
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_send(event, expected)
        ctx.should_finished(matcher)

    cleanup()
    getimg.image_fetch = _image_fetch


code_test_terminate = """\
await feedback("test 1")
await sleep(1)
await feedback("test 2")
"""


@pytest.mark.asyncio
async def test_terminate_1(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.matchers.terminate import matcher

    async with app.test_matcher(matcher) as ctx:
        bot = fake_v11_bot(ctx)
        event = fake_v11_group_message_event(
            group_id=exe_code_group,
            user_id=superuser,
            message=Message("terminate"),
        )
        cleanup = make_v11_session_cache(bot, event)
        async with ensure_context(bot, event):
            await Context.execute(bot, event, "")
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_finished(matcher)
    cleanup()


@pytest.mark.asyncio
async def test_terminate_2(app: App) -> None:
    # sourcery skip: use-fstring-for-concatenation
    from nonebot_plugin_exe_code.matchers.terminate import matcher

    async with app.test_matcher(matcher) as ctx:
        bot = fake_v11_bot(ctx)
        target_id = fake_user_id()
        event = fake_v11_group_message_event(
            group_id=exe_code_group,
            user_id=superuser,
            message="terminate" + MessageSegment.at(target_id),
        )
        cleanup = make_v11_session_cache(bot, event)
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_send(
            event,
            "获取 Context 失败: "
            f"SessionNotInitialized: None, key=('{target_id}', '{bot.type}')",
        )

    cleanup()


@pytest.mark.asyncio
async def test_terminate_3(app: App) -> None:
    # sourcery skip: use-fstring-for-concatenation
    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.matchers.terminate import handle_terminate

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        user_id = fake_user_id()
        event = fake_v11_event(user_id)
        cleanup = make_v11_session_cache(bot, event)
        ctx.should_call_send(event, Message("test 1"))
        expected = "中止" + MessageSegment.at(user_id) + "的执行任务"
        ctx.should_call_send(event, expected)

        async def _test1() -> None:
            with pytest.raises(asyncio.CancelledError):
                await Context.execute(bot, event, code_test_terminate)

        async def _test2() -> None:
            await asyncio.sleep(0.05)
            with pytest.raises(FinishedException):
                await handle_terminate(
                    target=str(user_id),
                    context=Context.get_context(str(user_id)),
                )

        async with ensure_context(bot, event):
            await asyncio.gather(_test1(), _test2())
    cleanup()
