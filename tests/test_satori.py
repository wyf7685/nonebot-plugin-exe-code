import pytest
from nonebot.adapters.satori import Message
from nonebug import App

from .conftest import exe_code_group, exe_code_user, superuser
from .fake.common import fake_group_id, fake_user_id
from .fake.satori import (
    ensure_satori_api,
    fake_satori_bot,
    fake_satori_login,
    fake_satori_private_message_created_event,
    fake_satori_public_message_created_event,
)


@pytest.mark.anyio
async def test_satori_private(app: App) -> None:
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        bot = fake_satori_bot(ctx)
        event = fake_satori_private_message_created_event(
            user_id=str(superuser),
            content="code print(uid, gid)",
        )
        expected = Message(f"{superuser} private:{superuser}")
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_send(event, expected)
        ctx.should_finished(matcher)


@pytest.mark.anyio
async def test_satori_public(app: App) -> None:
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        bot = fake_satori_bot(ctx)
        user_id = str(fake_user_id())
        event = fake_satori_public_message_created_event(
            user_id=user_id,
            channel_id=str(exe_code_group),
            content="code print(uid, gid)",
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
            content="code print(uid, gid)",
        )
        expected = Message(f"{exe_code_user} {channel_id}")
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_send(event, expected)
        ctx.should_finished(matcher)


@pytest.mark.anyio
async def test_satori_set_mute(app: App) -> None:
    from nonebot_plugin_exe_code.exception import ParamMissing

    async with (
        app.test_api() as ctx,
        ensure_satori_api(ctx, channel_id=str(exe_code_group)) as api,
    ):
        ctx.should_call_api(
            "guild_member_mute",
            {
                "guild_id": str(exe_code_group),
                "user_id": api.event.user.id,
                "duration": 7685000.0,
            },
        )
        await api.set_mute(7685)

    async with app.test_api() as ctx, ensure_satori_api(ctx) as api:
        with pytest.raises(ParamMissing, match="未指定群组ID"):
            await api.set_mute(7685)


@pytest.mark.anyio
async def test_satori_mid(app: App) -> None:
    async with app.test_api() as ctx, ensure_satori_api(ctx) as api:
        assert api.mid == api.event.message.id


@pytest.mark.anyio
async def test_satori_set_reaction(app: App) -> None:
    from nonebot_plugin_exe_code.exception import ParamMissing

    async with (
        app.test_api() as ctx,
        ensure_satori_api(ctx, channel_id=str(exe_code_group)) as api,
    ):
        ctx.should_call_api(
            "reaction_create",
            {
                "channel_id": str(exe_code_group),
                "message_id": "10000",
                "emoji": "123",
            },
            result=None,
        )
        ctx.should_call_api(
            "reaction_create",
            {
                "channel_id": str(exe_code_group),
                "message_id": "10000",
                "emoji": "face:123",
            },
            result=None,
        )
        await api.set_reaction(123, api.mid)

    async with app.test_api() as ctx, ensure_satori_api(ctx) as api:
        with pytest.raises(ParamMissing, match="未指定群组ID"):
            await api.set_reaction(123, api.mid)


@pytest.mark.anyio
async def test_satori_get_platform(app: App) -> None:
    async with app.test_api() as ctx, ensure_satori_api(ctx) as api:
        ctx.should_call_api("login_get", {}, fake_satori_login())
        assert await api.get_platform() == "[Satori] platform"
