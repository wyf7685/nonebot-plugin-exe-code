import pytest
from nonebot.adapters.telegram import Message
from nonebot.adapters.telegram.exception import ActionFailed
from nonebot.adapters.telegram.model import ReactionTypeEmoji
from nonebug import App

from .conftest import exe_code_group, superuser
from .fake.common import ensure_context, fake_user_id
from .fake.telegram import (
    fake_telegram_bot,
    fake_telegram_event_session,
    fake_telegram_group_message_event,
    fake_telegram_private_message_event,
)


@pytest.mark.asyncio
async def test_telegram_private(app: App) -> None:
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        bot = fake_telegram_bot(ctx)
        event = fake_telegram_private_message_event(
            user_id=superuser,
            message=Message("code print(uid, gid)"),
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
            message=Message("code print(uid, gid)"),
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


@pytest.mark.asyncio
async def test_telegram_set_reaction(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.exception import APICallFailed, ParamMismatch

    async with app.test_api() as ctx:
        bot = fake_telegram_bot(ctx)
        event, _ = fake_telegram_event_session(bot)
        event.message_id = 222
        event.reply_to_message = fake_telegram_private_message_event(message_id=111)

        with ensure_context(bot, event), pytest.raises(ParamMismatch):
            await Context.execute(
                bot, event, "await api.set_reaction('👍', message_id='aaa')"
            )

        with ensure_context(bot, event), pytest.raises(ParamMismatch):
            await Context.execute(
                bot, event, "await api.set_reaction('👍', chat_id='bbb')"
            )

        ctx.should_call_api(
            "set_message_reaction",
            {
                "chat_id": 10000,
                "message_id": 111,
                "reaction": [ReactionTypeEmoji(type="emoji", emoji="👍")],
                "is_big": None,
            },
            result=True,
        )
        with ensure_context(bot, event):
            await Context.execute(bot, event, "await api.set_reaction('👍')")

        ctx.should_call_api(
            "set_message_reaction",
            {
                "chat_id": 10000,
                "message_id": 111,
                "reaction": [ReactionTypeEmoji(type="emoji", emoji="👍")],
                "is_big": None,
            },
            exception=ActionFailed("test"),
        )
        with ensure_context(bot, event), pytest.raises(APICallFailed):
            await Context.execute(bot, event, "await api.set_reaction('👍')")
