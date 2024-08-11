import pytest
from nonebot.adapters.onebot.v11 import (
    ActionFailed,
    Adapter,
    Bot,
    Message,
    MessageSegment,
)
from nonebug import App

from tests.conftest import exe_code_group
from tests.fake import fake_group_exe_code, fake_user_id

code_test_ob11_img_summary = """await api.img_summary("test")"""


@pytest.mark.asyncio()
async def test_ob11_img_summary(app: App):
    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.matchers.code import matcher

    url = "http://localhost:8080/image.png"
    expected = Message(MessageSegment.image(url))
    expected[0].data["summary"] = "test"

    async with app.test_matcher(matcher) as ctx:
        adapter = ctx.create_adapter(base=Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        bot.adapter.__class__.get_name = Adapter.get_name

        user_id = fake_user_id()
        Context.get_context(str(user_id)).set_value("gurl", url)
        event = fake_group_exe_code(
            exe_code_group,
            user_id,
            code_test_ob11_img_summary,
        )
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_api(
            "get_group_member_info",
            {"group_id": exe_code_group, "user_id": user_id},
            {"user_id": user_id, "sex": "unkown", "card": "", "nickname": ""},
        )
        ctx.should_call_send(event, expected)


code_test_ob11_recall = """await recall(1)"""


@pytest.mark.asyncio()
async def test_ob11_recall(app: App):
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        adapter = ctx.create_adapter(base=Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        bot.adapter.__class__.get_name = Adapter.get_name

        user_id = fake_user_id()
        event = fake_group_exe_code(
            exe_code_group,
            user_id,
            code_test_ob11_recall,
        )
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_api(
            "get_group_member_info",
            {"group_id": exe_code_group, "user_id": user_id},
            {"user_id": user_id, "sex": "unkown", "card": "", "nickname": ""},
        )
        ctx.should_call_api("delete_msg", {"message_id": 1}, {})


code_test_ob11_get_msg = """print(await get_msg(1))"""


@pytest.mark.asyncio()
async def test_ob11_get_msg(app: App):
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        adapter = ctx.create_adapter(base=Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        bot.adapter.__class__.get_name = Adapter.get_name

        user_id = fake_user_id()
        event = fake_group_exe_code(
            exe_code_group,
            user_id,
            code_test_ob11_get_msg,
        )
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_api(
            "get_group_member_info",
            {"group_id": exe_code_group, "user_id": user_id},
            {"user_id": user_id, "sex": "unkown", "card": "", "nickname": ""},
        )
        ctx.should_call_api(
            "get_msg",
            {"message_id": 1},
            {"raw_message": "123"},
        )
        ctx.should_call_send(event, Message("123"))


code_test_ob11_get_fwd = """print((await get_fwd(1))[0])"""


@pytest.mark.asyncio()
async def test_ob11_get_fwd(app: App):
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        adapter = ctx.create_adapter(base=Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        bot.adapter.__class__.get_name = Adapter.get_name

        user_id = fake_user_id()
        event = fake_group_exe_code(
            exe_code_group,
            user_id,
            code_test_ob11_get_fwd,
        )
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_api(
            "get_group_member_info",
            {"group_id": exe_code_group, "user_id": user_id},
            {"user_id": user_id, "sex": "unkown", "card": "", "nickname": ""},
        )
        ctx.should_call_api(
            "get_forward_msg",
            {"message_id": 1},
            {"messages": [{"raw_message": "123"}]},
        )
        ctx.should_call_send(event, Message("123"))


code_test_ob11_exception_1 = """\
res = await api.not_an_action(arg=123)
raise res.error
"""


@pytest.mark.asyncio()
async def test_ob11_exception_1(app: App):
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        adapter = ctx.create_adapter(base=Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        bot.adapter.__class__.get_name = Adapter.get_name

        user_id = fake_user_id()
        event = fake_group_exe_code(
            exe_code_group,
            user_id,
            code_test_ob11_exception_1,
        )
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_api(
            "get_group_member_info",
            {"group_id": exe_code_group, "user_id": user_id},
            {"user_id": user_id, "sex": "unkown", "card": "", "nickname": ""},
        )
        ctx.should_call_api(
            "not_an_action",
            {"arg": 123},
            exception=ActionFailed(),
        )
        ctx.should_call_send(event, Message("执行失败: ActionFailed()"))


code_test_ob11_exception_2 = """print(await api.not_an_action(arg=123))"""


@pytest.mark.asyncio()
async def test_ob11_exception_2(app: App):
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        adapter = ctx.create_adapter(base=Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        bot.adapter.__class__.get_name = Adapter.get_name

        user_id = fake_user_id()
        event = fake_group_exe_code(
            exe_code_group,
            user_id,
            code_test_ob11_exception_2,
        )
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_api(
            "get_group_member_info",
            {"group_id": exe_code_group, "user_id": user_id},
            {"user_id": user_id, "sex": "unkown", "card": "", "nickname": ""},
        )
        ctx.should_call_api(
            "not_an_action",
            {"arg": 123},
            exception=Exception(),
        )
        ctx.should_call_send(event, Message("<Result error=Exception()>"))


code_test_ob11_exception_3 = """\
try:
    await api.not_an_action(arg=123, raise_text="TEST")
except Exception as err:
    print(repr(err))
"""


@pytest.mark.asyncio()
async def test_ob11_exception_3(app: App):
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        adapter = ctx.create_adapter(base=Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        bot.adapter.__class__.get_name = Adapter.get_name

        user_id = fake_user_id()
        event = fake_group_exe_code(
            exe_code_group,
            user_id,
            code_test_ob11_exception_3,
        )
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_api(
            "get_group_member_info",
            {"group_id": exe_code_group, "user_id": user_id},
            {"user_id": user_id, "sex": "unkown", "card": "", "nickname": ""},
        )
        ctx.should_call_api(
            "not_an_action",
            {"arg": 123},
            exception=Exception(),
        )
        ctx.should_call_send(event, Message("RuntimeError('TEST')"))
