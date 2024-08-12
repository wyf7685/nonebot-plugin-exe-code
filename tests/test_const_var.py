import pytest
from nonebot.adapters.onebot.v11 import Adapter, Bot, Message
from nonebug import App

from tests.conftest import exe_code_group
from tests.fake import fake_user_id, fake_v11_group_exe_code

code_test_const_var_1 = """\
api.set_const("test_var", {"a":[1, "2"]})
"""

code_test_const_var_2 = """\
print(test_var["a"][0])
api.set_const("test_var")
reset()
"""

code_test_invalid_const_var = """\
api.set_const('@@@', 123)
"""


@pytest.mark.asyncio()
async def test_const_var(app: App):
    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        adapter = ctx.create_adapter(base=Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        bot.adapter.__class__.get_name = Adapter.get_name

        user_id = fake_user_id()
        event = fake_v11_group_exe_code(
            exe_code_group,
            user_id,
            code_test_const_var_1,
        )
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_api(
            "get_group_member_info",
            {"group_id": exe_code_group, "user_id": user_id},
            {"user_id": user_id, "sex": "unkown", "card": "", "nickname": ""},
        )

        event = fake_v11_group_exe_code(
            exe_code_group,
            user_id,
            code_test_const_var_2,
        )
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_send(event, Message("1"))

    context = Context.get_context(str(user_id)).ctx
    assert context.get("test_var") is None


@pytest.mark.asyncio()
async def test_invalid_const_var(app: App):
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        adapter = ctx.create_adapter(base=Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        bot.adapter.__class__.get_name = Adapter.get_name

        user_id = fake_user_id()
        event = fake_v11_group_exe_code(
            exe_code_group,
            user_id,
            code_test_invalid_const_var,
        )
        expected = Message("""执行失败: ValueError("'@@@' 不是合法的 Python 标识符")""")
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_api(
            "get_group_member_info",
            {"group_id": exe_code_group, "user_id": user_id},
            {"user_id": user_id, "sex": "unkown", "card": "", "nickname": ""},
        )
        ctx.should_call_send(event, expected)
