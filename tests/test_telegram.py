import pytest
from nonebot.adapters.telegram import Message
from nonebug import App

from tests.conftest import exe_code_group, superuser
from tests.fake import (
    fake_telegram_bot,
    fake_telegram_group_message_event,
    fake_telegram_private_message_event,
    fake_user_id,
)


@pytest.mark.asyncio
async def test_telegram_private(app: App):
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        bot = fake_telegram_bot(ctx)
        event = fake_telegram_private_message_event(
            user_id=superuser,
            message=Message("code print(qid, gid)"),
        )
        expected = Message(f"{superuser} None")
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_api(
            "get_chat",
            {"chat_id": superuser},
            {"id": superuser, "type": "private"},
        )
        ctx.should_call_api(
            "get_user_profile_photos",
            {"user_id": superuser, "limit": 1, "offset": None},
            {"total_count": 0, "photos": []},
        )
        ctx.should_call_send(event, expected, reply_markup=None)
        ctx.should_finished(matcher)


@pytest.mark.asyncio
async def test_telegram_group(app: App):
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        bot = fake_telegram_bot(ctx)
        user_id = fake_user_id()
        event = fake_telegram_group_message_event(
            user_id=user_id,
            group_id=exe_code_group,
            message=Message("code print(qid, gid)"),
        )
        expected = Message(f"{user_id} {exe_code_group}")
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_api(
            "get_chat_member",
            {"chat_id": exe_code_group, "user_id": user_id},
            {
                "status": "member",
                "user": {
                    "id": user_id,
                    "is_bot": False,
                    "first_name": "name",
                },
            },
        )
        ctx.should_call_api(
            "get_user_profile_photos",
            {"user_id": user_id, "limit": 1, "offset": None},
            {"total_count": 0, "photos": []},
        )
        ctx.should_call_send(event, expected, reply_markup=None)
        ctx.should_finished(matcher)
