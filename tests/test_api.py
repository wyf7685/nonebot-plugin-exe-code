# ruff: noqa: S101, N814

import asyncio

import httpx
import pytest
import respx
from nonebot.adapters.console import Message as ConsoleMessage
from nonebot.adapters.onebot.v11 import Message as V11Message
from nonebot.adapters.onebot.v11 import MessageSegment as V11MS
from nonebot.adapters.onebot.v11.event import Reply, Sender
from nonebot.adapters.satori import Message as SatoriMessage
from nonebot.adapters.satori import MessageSegment as SatoriMessageSegment
from nonebug import App

from .conftest import exe_code_group, superuser
from .fake.common import ensure_context, fake_group_id, fake_user_id
from .fake.console import fake_console_bot, fake_console_event_session
from .fake.onebot11 import (
    fake_v11_bot,
    fake_v11_event_session,
    fake_v11_group_message_event,
)
from .fake.satori import fake_satori_bot, fake_satori_event_session


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
        expected = V11Message(f"api.{help_desc.format()}")
        ctx.should_call_send(event, expected)
        with ensure_context(bot, event):
            await Context.execute(bot, event, "await help(api.set_const)")


@pytest.mark.asyncio
async def test_help(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.exception import NoMethodDescription
    from nonebot_plugin_exe_code.interface.adapters.onebot11 import API
    from nonebot_plugin_exe_code.interface.user import User
    from nonebot_plugin_exe_code.interface.utils import get_method_description

    content, description = API.get_all_description()
    expected = [
        V11MS.node_custom(0, "forward", V11Message(V11MS.text(msg)))
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

    async with app.test_api() as ctx:
        bot = fake_satori_bot(ctx)
        event, _ = fake_satori_event_session(bot)

        desc = get_method_description(API.set_const)
        assert desc is not None
        expected = SatoriMessage(SatoriMessageSegment.text(f"api.{desc.format()}"))
        ctx.should_call_send(event, expected)
        with ensure_context(bot, event):
            await Context.execute(bot, event, "await help(api.set_const)")

        desc = get_method_description(User.send)
        assert desc is not None
        expected = SatoriMessage(SatoriMessageSegment.text(f"usr.{desc.format()}"))
        ctx.should_call_send(event, expected)
        with ensure_context(bot, event):
            await Context.execute(bot, event, "await help(user('').send)")

        with (
            ensure_context(bot, event),
            pytest.raises(NoMethodDescription),
        ):
            await Context.execute(bot, event, "await help(api.export)")


@pytest.mark.asyncio
@pytest.mark.usefixtures("app")
async def test_doc_annotation() -> None:
    from nonebot.adapters import Message

    from nonebot_plugin_exe_code.interface.help_doc import format_annotation

    assert format_annotation("test") == "test"
    assert format_annotation(int) == "int"
    assert format_annotation(str) == "str"
    assert format_annotation(None) == "None"
    assert format_annotation(Message) == "Message"


@pytest.mark.asyncio
async def test_buffer_size(app: App) -> None:
    from nonebot_plugin_exe_code.config import config
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot)

        original, config.buffer_size = config.buffer_size, 100
        ctx.should_call_send(event, V11Message("0" * 10))
        with ensure_context(bot, event), pytest.raises(OverflowError):
            await Context.execute(bot, event, "print('0' * 10); print('0' * 100)")
        config.buffer_size = original


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
                "message": V11Message("123"),
            },
            {},
        )
        with ensure_context(bot, event):
            await Context.execute(
                bot,
                event,
                f"sudo.set_usr({user_id})\n"
                f"sudo.set_grp({group_id})\n"
                "sudo.ctx(uid).var = 123\n"
                "await user(uid).send(str(var))\n",
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
            ctx.should_call_send(event, V11Message(str(i)))

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
        ctx.should_call_send(event, V11Message("False"))
        with ensure_context(bot, event):
            await Context.execute(bot, event, code)

        event, _ = fake_v11_event_session(bot, group_id=fake_group_id())
        ctx.should_call_send(event, V11Message("True"))
        with ensure_context(bot, event):
            await Context.execute(bot, event, code)


@pytest.mark.asyncio
async def test_send_private_forward(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot)
        expected = [
            V11MS.node_custom(0, "forward", V11Message("1")),
            V11MS.node_custom(0, "forward", V11Message("2")),
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
                'await user(uid).send_fwd(["1", "2"])',
            )


@pytest.mark.asyncio
async def test_send_group_forward(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot, group_id=exe_code_group)
        expected = [
            V11MS.node_custom(0, "forward", V11Message("1")),
            V11MS.node_custom(0, "forward", V11Message("2")),
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


@pytest.mark.asyncio
async def test_api_input(app: App) -> None:
    from nonebot.message import handle_event

    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.matchers.code import matcher

    prompt = V11Message("test-prompt")
    expected = V11Message("test-input")

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
                await Context.execute(
                    bot,
                    event,
                    'print(await api.input("test-prompt"))',
                )

        async def _test2() -> None:
            await asyncio.sleep(0.1)
            await handle_event(bot, input_event)

        await asyncio.gather(_test1(), _test2())


@pytest.mark.asyncio
async def test_api_input_timeout(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.matchers.code import matcher

    prompt = V11Message("test-prompt")

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot, superuser, exe_code_group)
        ctx.should_call_send(event, prompt)

        with ensure_context(bot, event, matcher()), pytest.raises(TimeoutError):
            await Context.execute(
                bot,
                event,
                'print(await api.input("test-prompt", timeout=0.01))',
            )


@pytest.mark.asyncio
async def test_api_type_mismatch(app: App) -> None:
    from nonebot_plugin_exe_code.exception import BotEventMismatch
    from nonebot_plugin_exe_code.interface.adapters.satori import API

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, session = fake_v11_event_session(bot, superuser, exe_code_group)

        with pytest.raises(BotEventMismatch, match="Bot/Event type mismatch"):
            API(bot, event, session, {})  # pyright: ignore[reportArgumentType]


@pytest.mark.asyncio
async def test_api_get_platform(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_console_bot(ctx)
        event, _ = fake_console_event_session(bot)

        ctx.should_call_send(event, ConsoleMessage("Console"))
        with ensure_context(bot, event):
            await Context.execute(bot, event, "print(await api.get_platform())")


@pytest.mark.asyncio
async def test_api_reply_id(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot)
        event.reply = Reply(
            time=1000000,
            message_type="test",
            message_id=123,
            real_id=1,
            sender=Sender(
                card="",
                nickname="test",
                role="member",
            ),
            message=V11Message(),
        )

        ctx.should_call_send(event, V11Message("123"))
        with ensure_context(bot, event):
            await Context.execute(bot, event, "print(await reply_id())")


@respx.mock
@pytest.mark.asyncio
async def test_api_http_request(app: App) -> None:  # noqa: ARG001
    from nonebot_plugin_exe_code.interface.http import Http

    url = "https://example.com/"
    return_value = httpx.Response(200, content=b"test")

    route_get = respx.get(url).mock(return_value)
    resp = (await Http().get(url)).raise_for_status()
    assert route_get.called
    assert resp.read() == b"test"
    request = route_get.calls.last.request
    assert request.method == "GET"
    assert str(request.url) == url

    route_post = respx.post(url).mock(return_value)
    resp = (await Http().post(url, json={"test": "test"})).raise_for_status()
    assert route_post.called
    assert resp.read() == b"test"
    request = route_post.calls.last.request
    assert request.method == "POST"
    assert str(request.url) == url
    assert request.headers["Content-Type"] == "application/json"
    assert request.content == b'{"test":"test"}'

    respx.clear()

    route_fail = respx.get(url).mock(httpx.Response(404, content=None))
    resp = await Http().get(url)
    assert route_fail.called
    with pytest.raises(RuntimeError):
        resp.raise_for_status().read()
