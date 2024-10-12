# ruff: noqa: S101

import asyncio

import pytest
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot.adapters.satori import Message as SatoriMessage
from nonebot.adapters.satori import MessageSegment as SatoriMessageSegment
from nonebug import App

from tests.conftest import exe_code_group, superuser
from tests.fake import (
    ensure_context,
    fake_group_id,
    fake_satori_bot,
    fake_satori_event_session,
    fake_user_id,
    fake_v11_bot,
    fake_v11_event_session,
    fake_v11_group_message_event,
)


@pytest.mark.asyncio
async def test_help_method(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.interface.api import API
    from nonebot_plugin_exe_code.interface.utils import get_method_description

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot)
        help_desc = get_method_description(API.set_const)
        assert help_desc is not None
        expected = Message(f"api.{help_desc.format()}")
        ctx.should_call_send(event, expected)
        with ensure_context(bot, event):
            await Context.execute(bot, event, "await help(api.set_const)")


@pytest.mark.asyncio
async def test_help(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.interface.adapters.onebot11 import API
    from nonebot_plugin_exe_code.interface.user import User
    from nonebot_plugin_exe_code.interface.utils import get_method_description

    content, description = API.get_all_description()
    expected = [
        MessageSegment.node_custom(0, "forward", Message(MessageSegment.text(msg)))
        for msg in [
            "   ===== API说明 =====   ",
            " - API说明文档 - 目录 - \n" + "\n".join(content),
            *description,
        ]
    ]

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot)

        ctx.should_call_api(
            "send_private_forward_msg",
            {
                "user_id": event.user_id,
                "messages": expected,
            },
            {},
        )
        with ensure_context(bot, event):
            await Context.execute(bot, event, "await help()")

    desc = get_method_description(API.set_const)
    assert desc is not None
    expected = SatoriMessage(SatoriMessageSegment.text(f"api.{desc.format()}"))
    async with app.test_api() as ctx:
        bot = fake_satori_bot(ctx)
        event, _ = fake_satori_event_session(bot)
        ctx.should_call_send(event, expected)
        with ensure_context(bot, event):
            await Context.execute(bot, event, "await help(api.set_const)")

    desc = get_method_description(User.send)
    assert desc is not None
    expected = SatoriMessage(SatoriMessageSegment.text(f"usr.{desc.format()}"))
    async with app.test_api() as ctx:
        bot = fake_satori_bot(ctx)
        event, _ = fake_satori_event_session(bot)
        ctx.should_call_send(event, expected)
        with ensure_context(bot, event):
            await Context.execute(bot, event, "await help(user('').send)")


@pytest.mark.asyncio
async def test_descriptor(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_satori_bot(ctx)
        event, _ = fake_satori_event_session(bot)
        with ensure_context(bot, event), pytest.raises(AttributeError):
            await Context.execute(bot, event, "api.feedback = None")

        with ensure_context(bot, event), pytest.raises(AttributeError):
            await Context.execute(bot, event, "del group('').send")

        with ensure_context(bot, event), pytest.raises(AttributeError):
            await Context.execute(bot, event, "api.abcd = None")


@pytest.mark.asyncio
async def test_superuser(app: App) -> None:
    from nonebot_plugin_exe_code.config import config
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot, superuser)
        user_id, group_id = fake_user_id(), fake_group_id()

        ctx.should_call_api(
            "send_msg",
            {
                "message_type": "private",
                "user_id": superuser,
                "message": Message("123"),
            },
            {},
        )
        with ensure_context(bot, event):
            await Context.execute(
                bot,
                event,
                f"sudo.set_usr({user_id})\n"
                f"sudo.set_grp({group_id})\n"
                "sudo.ctx(qid).var = 123\n"
                "await user(qid).send(str(var))\n",
            )

        assert str(user_id) in config.user
        assert str(group_id) in config.group


@pytest.mark.asyncio
async def test_send_limit(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.interface.utils import ReachLimit

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot)

        for i in range(6):
            ctx.should_call_send(event, Message(str(i)))

        with ensure_context(bot, event), pytest.raises(ReachLimit):
            await Context.execute(
                bot,
                event,
                "for i in range(7): await feedback(i)",
            )


@pytest.mark.asyncio
async def test_is_group(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        code = "print(api.is_group())"

        event, _ = fake_v11_event_session(bot)
        ctx.should_call_send(event, Message("False"))
        with ensure_context(bot, event):
            await Context.execute(bot, event, code)

        event, _ = fake_v11_event_session(bot, group_id=fake_group_id())
        ctx.should_call_send(event, Message("True"))
        with ensure_context(bot, event):
            await Context.execute(bot, event, code)


@pytest.mark.asyncio
async def test_send_private_forward(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot)
        expected = [
            MessageSegment.node_custom(0, "forward", Message("1")),
            MessageSegment.node_custom(0, "forward", Message("2")),
        ]
        ctx.should_call_api(
            "send_private_forward_msg",
            {
                "user_id": event.user_id,
                "messages": expected,
            },
            {},
        )
        with ensure_context(bot, event):
            await Context.execute(
                bot,
                event,
                'await user(qid).send_fwd(["1", "2"])',
            )


@pytest.mark.asyncio
async def test_send_group_forward(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot, group_id=exe_code_group)
        expected = [
            MessageSegment.node_custom(0, "forward", Message("1")),
            MessageSegment.node_custom(0, "forward", Message("2")),
        ]
        ctx.should_call_api(
            "send_group_forward_msg",
            {
                "group_id": exe_code_group,
                "messages": expected,
            },
            {},
        )
        with ensure_context(bot, event):
            await Context.execute(
                bot,
                event,
                'await group(gid).send_fwd(["1", "2"])',
            )


code_test_api_input = """\
print(await api.input("test-prompt"))
"""


@pytest.mark.asyncio
async def test_api_input(app: App) -> None:
    from nonebot.message import handle_event

    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.matchers.code import matcher

    prompt = Message("test-prompt")
    expected = Message("test-input")

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot, superuser, exe_code_group)
        input_event = fake_v11_group_message_event(
            user_id=superuser,
            group_id=exe_code_group,
            message=expected,
        )
        ctx.should_call_send(event, prompt)
        ctx.should_call_send(event, expected)

        async def _test1() -> None:
            with ensure_context(bot, event, matcher()):
                await Context.execute(bot, event, code_test_api_input)

        async def _test2() -> None:
            await asyncio.sleep(0.1)
            await handle_event(bot, input_event)

        await asyncio.gather(_test1(), _test2())


code_test_api_input_timeout = """\
print(await api.input("test-prompt", timeout=0.01))
"""


@pytest.mark.asyncio
async def test_api_input_timeout(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.matchers.code import matcher

    prompt = Message("test-prompt")

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot, superuser, exe_code_group)
        ctx.should_call_send(event, prompt)

        with ensure_context(bot, event, matcher()), pytest.raises(TimeoutError):
            await Context.execute(bot, event, code_test_api_input_timeout)


@pytest.mark.asyncio
async def test_api_type_mismatch(app: App) -> None:
    from nonebot_plugin_exe_code.interface.adapters.satori import API

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, session = fake_v11_event_session(bot, superuser, exe_code_group)

        with pytest.raises(RuntimeError, match="Bot/Event type mismatch"):
            API(bot, event, session, {})  # pyright: ignore[reportArgumentType]
