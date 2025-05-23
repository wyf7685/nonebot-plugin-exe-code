# ruff: noqa: S101

import pytest
from nonebot.adapters.onebot.v11 import Message
from nonebug import App

from .fake.common import ensure_context, fake_session, fake_user_id
from .fake.onebot11 import fake_v11_bot, fake_v11_event

code_test_const_var_1 = """\
api.set_const("test_var", {"a":[1, "2"]})
"""

code_test_const_var_2 = """\
print(test_var["a"][0])
api.set_const("test_var")
reset()
"""


@pytest.mark.asyncio
async def test_const_var(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        user_id = fake_user_id()

        event = fake_v11_event(user_id)
        async with ensure_context(bot, event):
            await Context.execute(bot, event, code_test_const_var_1)

        event = fake_v11_event(user_id)
        ctx.should_call_send(event, Message("1"))
        async with ensure_context(bot, event):
            await Context.execute(bot, event, code_test_const_var_2)

        session = await fake_session(bot, event)
        assert Context.get_context(session).ctx.get("test_var") is None


code_test_invalid_const_var_name = """\
api.set_const('@@@', 123)
"""


@pytest.mark.asyncio
async def test_invalid_const_var_name(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event = fake_v11_event()
        async with ensure_context(bot, event):
            with pytest.raises(ValueError, match="'@@@' 不是合法的 Python 标识符"):
                await Context.execute(bot, event, code_test_invalid_const_var_name)


code_test_invalid_const_var_value = """\
api.set_const('test_var', object())
"""


@pytest.mark.asyncio
async def test_invalid_const_var_value(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event = fake_v11_event()
        async with ensure_context(bot, event):
            with pytest.raises(TypeError, match="Invalid argument"):
                await Context.execute(bot, event, code_test_invalid_const_var_value)
