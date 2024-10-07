import pytest
from nonebot.adapters.telegram import Message
from nonebug import App

from tests.conftest import exe_code_group, superuser
from tests.fake import (
    ensure_context,
    fake_telegram_bot,
    fake_telegram_event_session,
    fake_telegram_group_message_event,
    fake_telegram_private_message_event,
    fake_user_id,
)


@pytest.mark.asyncio
async def test_telegram_private(app: App) -> None:
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
        ctx.should_call_send(event, expected, reply_markup=None)
        ctx.should_finished(matcher)


@pytest.mark.asyncio
async def test_telegram_group(app: App) -> None:
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
        ctx.should_call_send(event, expected, reply_markup=None)
        ctx.should_finished(matcher)


@pytest.mark.asyncio
async def test_telegram_mid(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_telegram_bot(ctx)
        event, _ = fake_telegram_event_session(bot)
        ctx.should_call_send(event, Message("1"), reply_markup=None)
        with ensure_context(bot, event):
            await Context.execute(bot, event, "print(api.mid)")
