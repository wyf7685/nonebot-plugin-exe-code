import pytest
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebug import App

from tests.conftest import exe_code_group
from tests.fake import fake_user_id, fake_v11_bot, fake_v11_group_exe_code

code_test_api_message = """\
await feedback(1)
await user(qid).send(MessageSegment.text("2"))
await group(gid).send(Text("3"))
print("4")
await sleep(0)
"""


@pytest.mark.asyncio
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


code_test_extract_code = (
    "print(" + MessageSegment.at(111) + ")\nprint(" + MessageSegment.image(b"") + ")\n"
)


@pytest.mark.asyncio
async def test_extract_code(app: App) -> None:
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        bot = fake_v11_bot(ctx)
        user_id = fake_user_id()
        event = fake_v11_group_exe_code(exe_code_group, user_id, code_test_extract_code)
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_send(event, Message("111\n[url]"))
        ctx.should_finished(matcher)

        event = fake_v11_group_exe_code(exe_code_group, user_id, code_test_extract_code)
        event.message = MessageSegment.at(111) + event.message
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)


code_test_return = """return '1234'"""


@pytest.mark.asyncio
async def test_return(app: App) -> None:
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        bot = fake_v11_bot(ctx)
        user_id = fake_user_id()
        event = fake_v11_group_exe_code(exe_code_group, user_id, code_test_return)
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_send(event, Message("'1234'"))
        ctx.should_finished(matcher)


code_test_exception = """a = 1 / 0"""


@pytest.mark.asyncio
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
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_send(
            event, Message("执行失败: ZeroDivisionError('division by zero')")
        )
        ctx.should_finished(matcher)
