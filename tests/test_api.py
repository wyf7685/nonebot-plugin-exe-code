import asyncio

import pytest
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebug import App

from tests.conftest import exe_code_group, superuser
from tests.fake import (
    ensure_context,
    fake_group_id,
    fake_user_id,
    fake_v11_bot,
    fake_v11_event_session,
    fake_v11_group_message_event,
)


@pytest.mark.asyncio()
async def test_help_method(app: App):
    from nonebot_plugin_exe_code.constant import INTERFACE_METHOD_DESCRIPTION
    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.interface.api import API
    from nonebot_plugin_exe_code.interface.help_doc import FuncDescription

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, session = fake_v11_event_session(bot)
        help_desc: FuncDescription = getattr(
            API.set_const, INTERFACE_METHOD_DESCRIPTION
        )
        expected = Message(f"api.{help_desc.format(API.set_const)}")
        ctx.should_call_send(event, expected)
        with ensure_context(bot, event):
            await Context.execute(bot, session, "await help(api.set_const)")


@pytest.mark.asyncio()
async def test_help(app: App):
    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.interface.adapter_api.onebot11 import API

    content, description = API._get_all_description()
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
        event, session = fake_v11_event_session(bot)

        ctx.should_call_api(
            "send_private_forward_msg",
            {
                "user_id": event.user_id,
                "messages": expected,
            },
            {},
        )
        with ensure_context(bot, event):
            await Context.execute(bot, session, "await help()")


@pytest.mark.asyncio()
async def test_superuser(app: App):
    from nonebot_plugin_exe_code.config import config
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, session = fake_v11_event_session(bot, superuser)
        user_id, group_id = fake_user_id(), fake_group_id()

        ctx.should_call_send(event, Message("123"))
        with ensure_context(bot, event):
            await Context.execute(
                bot,
                session,
                f"set_usr({user_id})\n"
                f"set_grp({group_id})\n"
                "get_ctx(qid)['var'] = 123\n"
                "print(var)",
            )

        assert str(user_id) in config.user
        assert str(group_id) in config.group


@pytest.mark.asyncio()
async def test_send_limit(app: App):
    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.interface.utils import ReachLimit

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, session = fake_v11_event_session(bot)

        for i in range(6):
            ctx.should_call_send(event, Message(str(i)))

        with ensure_context(bot, event):
            with pytest.raises(ReachLimit):
                await Context.execute(
                    bot,
                    session,
                    "for i in range(7): await feedback(i)",
                )


@pytest.mark.asyncio()
async def test_is_group(app: App):
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        code = "print(api.is_group())"

        event, session = fake_v11_event_session(bot)
        ctx.should_call_send(event, Message("False"))
        with ensure_context(bot, event):
            await Context.execute(bot, session, code)

        event, session = fake_v11_event_session(bot, group_id=fake_group_id())
        ctx.should_call_send(event, Message("True"))
        with ensure_context(bot, event):
            await Context.execute(bot, session, code)


@pytest.mark.asyncio()
async def test_feedback_forward(app: App):
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, session = fake_v11_event_session(bot)
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
                session,
                'await feedback(["1", "2"], fwd=True)',
            )


@pytest.mark.asyncio()
async def test_send_private_forward(app: App):
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, session = fake_v11_event_session(bot)
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
                session,
                'await user(qid).send_fwd(["1", "2"])',
            )


@pytest.mark.asyncio()
async def test_send_group_forward(app: App):
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, session = fake_v11_event_session(bot, group_id=exe_code_group)
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
                session,
                'await group(gid).send_fwd(["1", "2"])',
            )


code_test_api_input = """\
print(await api.input("test-prompt"))
"""


@pytest.mark.asyncio()
async def test_api_input(app: App):
    from nonebot.message import handle_event

    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.matchers.code import matcher

    prompt = Message("test-prompt")
    expected = Message("test-input")

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, session = fake_v11_event_session(bot, superuser, exe_code_group)
        input_event = fake_v11_group_message_event(
            user_id=superuser,
            group_id=exe_code_group,
            message=expected,
        )
        ctx.should_call_send(event, prompt)
        ctx.should_call_send(event, expected)

        async def _test1():
            with ensure_context(bot, event, matcher()):
                await Context.execute(bot, session, code_test_api_input)

        async def _test2():
            await asyncio.sleep(0.1)
            await handle_event(bot, input_event)

        await asyncio.gather(_test1(), _test2())
