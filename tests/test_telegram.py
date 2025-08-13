import pytest
from nonebot.adapters.telegram import Message
from nonebot.adapters.telegram.exception import ActionFailed
from nonebot.adapters.telegram.model import ReactionTypeEmoji
from nonebug import App

from .conftest import exe_code_group, superuser
from .fake.common import fake_user_id
from .fake.telegram import (
    ensure_telegram_api,
    fake_telegram_bot,
    fake_telegram_group_message_event,
    fake_telegram_private_message_event,
    make_telegram_session_cache,
)


@pytest.mark.anyio
async def test_telegram_private(app: App) -> None:
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        bot = fake_telegram_bot(ctx)
        event = fake_telegram_private_message_event(
            user_id=superuser,
            message=Message("code print(uid, gid)"),
        )
        cleanup = make_telegram_session_cache(bot, event)
        expected = Message(f"{superuser} None")
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_send(event, expected, reply_markup=None)
        ctx.should_finished(matcher)
    cleanup()


@pytest.mark.anyio
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
        cleanup = make_telegram_session_cache(bot, event)
        expected = Message(f"{user_id} {exe_code_group}")
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_send(event, expected, reply_markup=None)
        ctx.should_finished(matcher)
    cleanup()


@pytest.mark.anyio
async def test_telegram_mid(app: App) -> None:
    async with app.test_api() as ctx, ensure_telegram_api(ctx) as api:
        assert api.mid == str(api.event.message_id)


@pytest.mark.anyio
async def test_telegram_set_reaction(app: App) -> None:
    from nonebot_plugin_exe_code.exception import APICallFailed, ParamMismatch

    emoji = "👍"

    async with app.test_api() as ctx, ensure_telegram_api(ctx) as api:
        api.event.message_id = 222
        api.event.reply_to_message = fake_telegram_private_message_event(message_id=111)

        with pytest.raises(ParamMismatch):
            await api.set_reaction(emoji, message_id="aaa")

        with pytest.raises(ParamMismatch):
            await api.set_reaction(emoji, chat_id="bbb")

        ctx.should_call_api(
            "set_message_reaction",
            {
                "chat_id": 10000,
                "message_id": 111,
                "reaction": [ReactionTypeEmoji(type="emoji", emoji=emoji)],
                "is_big": None,
            },
            result=True,
        )
        await api.set_reaction(emoji)

        ctx.should_call_api(
            "set_message_reaction",
            {
                "chat_id": 10000,
                "message_id": 111,
                "reaction": [ReactionTypeEmoji(type="emoji", emoji=emoji)],
                "is_big": None,
            },
            exception=ActionFailed("test"),
        )
        with pytest.raises(APICallFailed):
            await api.set_reaction(emoji)
