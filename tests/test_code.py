import pytest
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebug import App

from .conftest import exe_code_group
from .fake.common import fake_user_id
from .fake.onebot11 import fake_v11_bot, fake_v11_group_exe_code, make_v11_session_cache

code_test_api_message = """\
await feedback(1)
await user(uid).send(MessageSegment.text("2"))
await group(gid).send(Text("3"))
print("4")
await sleep(0)
"""


@pytest.mark.anyio
async def test_api_message(app: App) -> None:
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        bot = fake_v11_bot(ctx)
        user_id = fake_user_id()
        event = fake_v11_group_exe_code(
            exe_code_group,
            user_id,
            code_test_api_message,
        )
        cleanup = make_v11_session_cache(bot, event)

        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_send(event, Message("1"))
        ctx.should_call_api(
            "send_msg",
            {
                "message_type": "private",
                "user_id": user_id,
                "message": Message("2"),
            },
        )
        ctx.should_call_api(
            "send_msg",
            {
                "message_type": "group",
                "group_id": exe_code_group,
                "message": Message("3"),
            },
        )
        ctx.should_call_send(event, Message("4"))
        ctx.should_finished(matcher)
    cleanup()


code_test_extract_code = (
    MessageSegment.text("print(")
    + MessageSegment.at(111)
    + MessageSegment.text(")\nprint(")
    + MessageSegment.image("https://example.com/image.png")
    + MessageSegment.text(")\n")
)


@pytest.mark.anyio
async def test_extract_code_1(app: App) -> None:
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        bot = fake_v11_bot(ctx)
        user_id = fake_user_id()
        event = fake_v11_group_exe_code(exe_code_group, user_id, code_test_extract_code)
        cleanup = make_v11_session_cache(bot, event)
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_send(event, Message("111\nhttps://example.com/image.png"))
        ctx.should_finished(matcher)
    cleanup()


@pytest.mark.anyio
async def test_extract_code_2(app: App) -> None:
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        bot = fake_v11_bot(ctx)
        user_id = fake_user_id()
        event = fake_v11_group_exe_code(exe_code_group, user_id, code_test_extract_code)
        cleanup = make_v11_session_cache(bot, event)
        event.message = MessageSegment.at(111) + event.message
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
    cleanup()


code_test_return = """return '1234'"""


@pytest.mark.anyio
async def test_return(app: App) -> None:
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        bot = fake_v11_bot(ctx)
        user_id = fake_user_id()
        event = fake_v11_group_exe_code(exe_code_group, user_id, code_test_return)
        cleanup = make_v11_session_cache(bot, event)

        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_send(event, Message("'1234'"))
        ctx.should_finished(matcher)
    cleanup()


code_test_exception = """a = 1 / 0"""


@pytest.mark.anyio
async def test_exception(app: App) -> None:
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        bot = fake_v11_bot(ctx)
        user_id = fake_user_id()
        event = fake_v11_group_exe_code(
            exe_code_group,
            user_id,
            code_test_exception,
        )
        cleanup = make_v11_session_cache(bot, event)

        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_send(
            event, Message("执行失败: ZeroDivisionError('division by zero')")
        )
        ctx.should_finished(matcher)
    cleanup()
