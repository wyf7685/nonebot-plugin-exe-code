import pytest
from nonebot.adapters.onebot.v11 import Adapter, Bot, Message, MessageSegment
from nonebot.adapters.onebot.v11.bot import _check_reply
from nonebot.adapters.onebot.v11.event import Reply
from nonebug import App

from tests.conftest import exe_code_group, superuser
from tests.fake import fake_img_bytes, fake_v11_group_message_event


@pytest.mark.asyncio()
async def test_getraw(app: App):
    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.matchers.getraw import matcher

    async with app.test_matcher(matcher) as ctx:
        adapter = ctx.create_adapter(base=Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        bot.adapter.__class__.get_name = Adapter.get_name

        reply_msg = MessageSegment.reply(123) + MessageSegment.at(456) + "789"
        msg = MessageSegment.reply(1) + "getraw"
        event = fake_v11_group_message_event(message=msg, user_id=superuser)
        expected = Message(MessageSegment.text(str(reply_msg)))

        ctx.should_call_api(
            "get_msg",
            {"message_id": 1},
            Reply(
                time=1000000,
                message_type="test",
                message_id=1,
                real_id=1,
                sender=event.sender,
                message=reply_msg,
            ),
        )
        await _check_reply(bot, event)
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_send(event, expected)

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
        adapter = ctx.create_adapter(base=Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        bot.adapter.__class__.get_name = Adapter.get_name

        reply_msg = MessageSegment.reply(123) + MessageSegment.at(456) + "789"
        msg = MessageSegment.reply(1) + "getmid"
        event = fake_v11_group_message_event(message=msg, user_id=superuser)
        expected = Message(str(1))

        ctx.should_call_api(
            "get_msg",
            {"message_id": 1},
            Reply(
                time=1000000,
                message_type="test",
                message_id=1,
                real_id=1,
                sender=event.sender,
                message=reply_msg,
            ),
        )
        await _check_reply(bot, event)
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_send(event, expected)

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
            adapter = ctx.create_adapter(base=Adapter)
            bot = ctx.create_bot(base=Bot, adapter=adapter)
            bot.adapter.__class__.get_name = Adapter.get_name

            reply_msg = "some" + MessageSegment.image(file=fake_img_bytes) + "text"
            msg = MessageSegment.reply(1) + "getimg"
            if varname is not None:
                msg += f" {varname}"
                msg.reduce()
            else:
                varname = "img"
            event = fake_v11_group_message_event(message=msg, user_id=superuser)

            ctx.should_call_api(
                "get_msg",
                {"message_id": 1},
                Reply(
                    time=1000000,
                    message_type="test",
                    message_id=1,
                    real_id=1,
                    sender=event.sender,
                    message=reply_msg,
                ),
            )
            await _check_reply(bot, event)
            ctx.receive_event(bot, event)
            ctx.should_pass_permission(matcher)
            if varname.isidentifier():
                expected = Message(f"图片已保存至变量 {varname}")
            else:
                expected = Message(f"{varname} 不是一个合法的 Python 标识符")
            ctx.should_call_send(event, expected)

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


# XXX: nonebug 似乎不支持同时处理多个 event
#      所以无法测试与 Context.task 相关的功能
# ref: nonebug.mixin.process:MatcherContext.run
#      nonebot_plugin_exe_code.context:Context

# code_test_terminate = """\
# await feedback("test 1")
# await sleep(1)
# await feedback("test 2")
# """


@pytest.mark.asyncio()
async def test_terminate(app: App):
    from nonebot_plugin_exe_code.matchers.code import matcher as m_code
    from nonebot_plugin_exe_code.matchers.terminate import matcher as m_terminate

    async with app.test_matcher([m_code, m_terminate]) as ctx:
        adapter = ctx.create_adapter(base=Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        bot.adapter.__class__.get_name = Adapter.get_name

        event = fake_v11_group_message_event(
            group_id=exe_code_group,
            user_id=superuser,
            message=Message("terminate"),
        )
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(m_terminate)

        # user_id = fake_user_id()
        # event = fake_group_exe_code(
        #     exe_code_group,
        #     user_id,
        #     code_test_terminate,
        # )
        # ctx.receive_event(bot, event)
        # ctx.should_pass_permission(m_code)
        # ctx.should_call_api(
        #     "get_group_member_info",
        #     {"group_id": exe_code_group, "user_id": user_id},
        #     {"user_id": user_id, "sex": "unkown", "card": "", "nickname": ""},
        # )
        # ctx.should_call_send(event, Message("test 1"))

        # event = fake_group_message_event_v11(
        #     group_id=exe_code_group,
        #     user_id=superuser,
        #     message="terminate" + MessageSegment.at(user_id),
        # )
        # ctx.receive_event(bot, event)
        # ctx.should_pass_permission(m_terminate)
        # expected = "中止" + MessageSegment.at(user_id) + "的执行任务"
        # ctx.should_call_send(event, expected)
