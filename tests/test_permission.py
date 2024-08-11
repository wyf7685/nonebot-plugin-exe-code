import pytest
from nonebot.adapters.onebot.v11 import Adapter, Bot
from nonebug import App

from tests.conftest import exe_code_group, exe_code_user, superuser
from tests.fake import (
    fake_group_exe_code,
    fake_private_exe_code,
    fake_group_id,
    fake_user_id,
)

fake_code = "a = 1"


@pytest.mark.asyncio()
async def test_superuser(app: App):
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        adapter = ctx.create_adapter(base=Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        bot.adapter.__class__.get_name = Adapter.get_name

        event = fake_private_exe_code(superuser, fake_code)
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_api(
            "get_stranger_info",
            {"user_id": superuser},
            {"user_id": superuser, "sex": "unkown", "card": "", "nickname": ""},
        )

        group_id = fake_group_id()
        event = fake_group_exe_code(group_id, superuser, fake_code)
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_api(
            "get_group_member_info",
            {"group_id": group_id, "user_id": superuser},
            {"user_id": superuser, "sex": "unkown", "card": "", "nickname": ""},
        )


@pytest.mark.asyncio()
async def test_exe_code_user(app: App):
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        adapter = ctx.create_adapter(base=Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        bot.adapter.__class__.get_name = Adapter.get_name

        event = fake_private_exe_code(exe_code_user, fake_code)
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_api(
            "get_stranger_info",
            {"user_id": exe_code_user},
            {"user_id": exe_code_user, "sex": "unkown", "card": "", "nickname": ""},
        )

        group_id = fake_group_id()
        event = fake_group_exe_code(group_id, exe_code_user, fake_code)
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_api(
            "get_group_member_info",
            {"group_id": group_id, "user_id": exe_code_user},
            {"user_id": exe_code_user, "sex": "unkown", "card": "", "nickname": ""},
        )


@pytest.mark.asyncio()
async def test_exe_code_group(app: App):
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        adapter = ctx.create_adapter(base=Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        bot.adapter.__class__.get_name = Adapter.get_name

        user_id = fake_user_id()
        event = fake_group_exe_code(exe_code_group, user_id, fake_code)
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_api(
            "get_group_member_info",
            {"group_id": exe_code_group, "user_id": user_id},
            {"user_id": user_id, "sex": "unkown", "card": "", "nickname": ""},
        )


@pytest.mark.asyncio()
async def test_not_allow(app: App):
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        adapter = ctx.create_adapter(base=Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        bot.adapter.__class__.get_name = Adapter.get_name

        user_id = fake_user_id()
        event = fake_private_exe_code(user_id, fake_code)
        ctx.receive_event(bot, event)
        ctx.should_not_pass_permission(matcher)

        group_id = fake_group_id()
        event = fake_group_exe_code(group_id, user_id, fake_code)
        ctx.receive_event(bot, event)
        ctx.should_not_pass_permission(matcher)
