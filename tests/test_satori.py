import pytest
from nonebot.adapters.satori import Message
from nonebug import App

from tests.conftest import exe_code_group, exe_code_user, superuser
from tests.fake import (
    ensure_context,
    fake_group_id,
    fake_satori_bot,
    fake_satori_event_session,
    fake_satori_private_message_created_event,
    fake_satori_public_message_created_event,
    fake_user_id,
)


@pytest.mark.asyncio
async def test_satori_private(app: App) -> None:
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        bot = fake_satori_bot(ctx)
        event = fake_satori_private_message_created_event(
            user_id=str(superuser),
            content="code print(qid, gid)",
        )
        expected = Message(f"{superuser} private:{superuser}")
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_send(event, expected)
        ctx.should_finished(matcher)


@pytest.mark.asyncio
async def test_satori_public(app: App) -> None:
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        bot = fake_satori_bot(ctx)
        user_id = str(fake_user_id())
        event = fake_satori_public_message_created_event(
            user_id=user_id,
            channel_id=str(exe_code_group),
            content="code print(qid, gid)",
        )
        expected = Message(f"{user_id} {exe_code_group}")
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_send(event, expected)
        ctx.should_finished(matcher)

        channel_id = str(fake_group_id())
        event = fake_satori_public_message_created_event(
            user_id=str(exe_code_user),
            channel_id=channel_id,
            content="code print(qid, gid)",
        )
        expected = Message(f"{exe_code_user} {channel_id}")
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_send(event, expected)
        ctx.should_finished(matcher)


code_test_satori_set_mute = """\
await api.set_mute(7685)
"""


@pytest.mark.asyncio
async def test_satori_set_mute(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_satori_bot(ctx)
        event, _ = fake_satori_event_session(bot, channel_id=str(exe_code_group))
        ctx.should_call_api(
            "guild_member_mute",
            {
                "guild_id": str(exe_code_group),
                "user_id": event.user.id,
                "duration": 7685000.0,
            },
        )
        with ensure_context(bot, event):
            await Context.execute(bot, event, code_test_satori_set_mute)

        event, _ = fake_satori_event_session(bot)
        with (
            ensure_context(bot, event),
            pytest.raises(ValueError, match="未指定群组ID"),
        ):
            await Context.execute(bot, event, code_test_satori_set_mute)


@pytest.mark.asyncio
async def test_satori_mid(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_satori_bot(ctx)
        event, _ = fake_satori_event_session(bot)
        ctx.should_call_send(event, Message("10000"))
        with ensure_context(bot, event):
            await Context.execute(bot, event, "print(api.mid)")


code_test_satori_set_reaction = """\
await api.set_reaction(123, api.mid)
"""


@pytest.mark.asyncio
async def test_satori_set_reaction(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_satori_bot(ctx)

        event, _ = fake_satori_event_session(bot, channel_id=str(exe_code_group))
        ctx.should_call_api(
            "reaction_create",
            {
                "channel_id": str(exe_code_group),
                "message_id": "10000",
                "emoji": "face:123",
            },
            result=None,
        )
        with ensure_context(bot, event):
            await Context.execute(bot, event, code_test_satori_set_reaction)

        event, _ = fake_satori_event_session(bot)
        with (
            ensure_context(bot, event),
            pytest.raises(ValueError, match="未指定群组ID"),
        ):
            await Context.execute(bot, event, code_test_satori_set_reaction)
