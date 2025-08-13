from typing import Any, cast

import anyio
import httpx
import pytest
import respx
from nonebot.adapters.console import Message as ConsoleMessage
from nonebot.adapters.onebot.v11 import Message as V11Message
from nonebot.adapters.onebot.v11 import MessageSegment as V11MS  #  noqa: N814
from nonebot.adapters.onebot.v11.event import Reply, Sender
from nonebot.adapters.satori import Message as SatoriMessage
from nonebot.adapters.satori import MessageSegment as SatoriMessageSegment
from nonebug import App

from .conftest import exe_code_group, superuser
from .fake.common import (
    ensure_context,
    fake_api,
    fake_group_id,
    fake_session,
    fake_user_id,
)
from .fake.console import fake_console_bot, fake_console_event
from .fake.onebot11 import (
    ensure_v11_session_cache,
    fake_v11_bot,
    fake_v11_event,
    fake_v11_group_message_event,
)
from .fake.satori import fake_satori_bot, fake_satori_event


@pytest.mark.anyio
async def test_help_method(app: App) -> None:
    from nonebot_plugin_exe_code.interface.utils import get_method_description

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event = fake_v11_event()
        async with ensure_context(bot, event) as api:
            help_desc = get_method_description(api.set_const)
            assert help_desc is not None
            expected = V11Message(f"api.{help_desc.format()}")
            ctx.should_call_send(event, expected)
            await api.help(api.set_const)


@pytest.mark.anyio
async def test_help(app: App) -> None:
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
        event = fake_v11_event()

        ctx.should_call_api(
            "send_private_forward_msg",
            {
                "user_id": event.user_id,
                "messages": expected,
            },
            {},
        )
        async with ensure_context(bot, event) as api:
            await api.help()

    async with app.test_api() as ctx:
        bot = fake_satori_bot(ctx)
        event = fake_satori_event()

        desc = get_method_description(API.set_const)
        assert desc is not None
        expected = SatoriMessage(SatoriMessageSegment.text(f"api.{desc.format()}"))
        ctx.should_call_send(event, expected)
        async with ensure_context(bot, event) as api:
            await api.help(API.set_const)

        desc = get_method_description(User.send)
        assert desc is not None
        expected = SatoriMessage(SatoriMessageSegment.text(f"usr.{desc.format()}"))
        ctx.should_call_send(event, expected)
        async with ensure_context(bot, event) as api:
            await api.help(api.user("").send)

        async with ensure_context(bot, event) as api:
            with pytest.raises(NoMethodDescription):
                await api.help(api.export)


@pytest.mark.anyio
@pytest.mark.usefixtures("app")
async def test_doc_annotation() -> None:
    from nonebot.adapters import Message

    from nonebot_plugin_exe_code.interface.help_doc import format_annotation

    assert format_annotation("test") == "test"
    assert format_annotation(int) == "int"
    assert format_annotation(str) == "str"
    assert format_annotation(None) == "None"
    assert format_annotation(Message) == "Message"


@pytest.mark.anyio
async def test_buffer_size(app: App) -> None:
    from nonebot_plugin_exe_code.config import config
    from nonebot_plugin_exe_code.interface.utils import Buffer

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event = fake_v11_event()
        api = await fake_api(bot, event)

        original, config.buffer_size = config.buffer_size, 100
        try:
            api.print("0" * 10)
            assert Buffer.get(api.uin).read() == "0" * 10 + "\n"
            with pytest.raises(OverflowError):
                api.print("0" * 101)
        finally:
            config.buffer_size = original


@pytest.mark.anyio
async def test_descriptor(app: App) -> None:
    async with app.test_api() as ctx:
        bot = fake_satori_bot(ctx)
        event = fake_satori_event()

        async with ensure_context(bot, event) as api:
            with pytest.raises(AttributeError):
                api.feedback = None  # pyright: ignore[reportAttributeAccessIssue]
            with pytest.raises(AttributeError):
                del api.group("").send
            with pytest.raises(AttributeError):
                api.abcd = None  # pyright: ignore[reportAttributeAccessIssue]


@pytest.mark.anyio
async def test_superuser(app: App) -> None:
    from nonebot_plugin_exe_code.config import config
    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.interface.utils import _Sudo as Sudo

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event = fake_v11_event(superuser)
        user_id, group_id = fake_user_id(), fake_group_id()
        _ = Context.get_context(await fake_session(bot, fake_v11_event(user_id)))

        ctx.should_call_api(
            "send_msg",
            {
                "message_type": "private",
                "user_id": user_id,
                "message": V11Message("123"),
            },
            {},
        )
        async with ensure_context(bot, event) as api:
            sudo = Sudo()
            sudo.set_usr(user_id)
            sudo.set_grp(group_id)
            target_ctx = cast(Any, sudo.ctx(user_id))
            target_ctx.var = 123
            await api.user(user_id).send(str(target_ctx.var))

        assert str(user_id) in config.user
        assert str(group_id) in config.group


@pytest.mark.anyio
async def test_send_limit(app: App) -> None:
    from nonebot_plugin_exe_code.interface.utils import ReachLimit

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event = fake_v11_event()

        for i in range(6):
            ctx.should_call_send(event, V11Message(str(i)))

        async with ensure_context(bot, event) as api:
            for i in range(6):
                await api.feedback(i)
            with pytest.raises(ReachLimit):
                await api.feedback(6)


@pytest.mark.anyio
async def test_is_group(app: App) -> None:
    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)

        event = fake_v11_event()
        with ensure_v11_session_cache(bot, event):
            async with ensure_context(bot, event) as api:
                assert not api.is_group()

        event = fake_v11_event(group_id=fake_group_id())
        with ensure_v11_session_cache(bot, event):
            async with ensure_context(bot, event) as api:
                assert api.is_group()


@pytest.mark.anyio
async def test_send_private_forward(app: App) -> None:
    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event = fake_v11_event()
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
        async with ensure_context(bot, event) as api:
            await api.user(event.user_id).send_fwd(["1", "2"])


@pytest.mark.anyio
async def test_send_group_forward(app: App) -> None:
    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event = fake_v11_event(group_id=exe_code_group)
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
        with ensure_v11_session_cache(bot, event):
            async with ensure_context(bot, event) as api:
                await api.group(exe_code_group).send_fwd(["1", "2"])


@pytest.mark.anyio
async def test_api_input(app: App) -> None:
    from nonebot.message import handle_event

    from nonebot_plugin_exe_code.matchers.code import matcher

    prompt = V11Message("test-prompt")
    expected = V11Message("test-input")

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event = fake_v11_event(superuser, exe_code_group)
        input_event = fake_v11_group_message_event(
            user_id=superuser,
            group_id=exe_code_group,
            message=expected,
        )
        ctx.should_call_send(event, prompt)
        ctx.should_call_send(event, expected)

        async def _test1() -> None:
            async with ensure_context(bot, event, matcher()) as api:
                await api.feedback(await api.input(prompt))

        async def _test2() -> None:
            await anyio.sleep(0.1)
            await handle_event(bot, input_event)

        with ensure_v11_session_cache(bot, event):
            async with anyio.create_task_group() as tg:
                tg.start_soon(_test1)
                tg.start_soon(_test2)


@pytest.mark.anyio
async def test_api_input_timeout(app: App) -> None:
    from nonebot_plugin_exe_code.matchers.code import matcher

    prompt = V11Message("test-prompt")

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event = fake_v11_event(superuser, exe_code_group)
        ctx.should_call_send(event, prompt)

        with ensure_v11_session_cache(bot, event):
            async with ensure_context(bot, event, matcher()) as api:
                with pytest.raises(TimeoutError):
                    await api.input(prompt, timeout=0.01)


@pytest.mark.anyio
async def test_api_type_mismatch(app: App) -> None:
    from nonebot_plugin_exe_code.exception import BotEventMismatch
    from nonebot_plugin_exe_code.interface.adapters.satori import API

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event = fake_v11_event(superuser, exe_code_group)
        with ensure_v11_session_cache(bot, event):
            session = await fake_session(bot, event)

        with pytest.raises(BotEventMismatch, match="Bot/Event type mismatch"):
            API(bot, event, session, {})  # pyright: ignore[reportArgumentType]


@pytest.mark.anyio
async def test_api_get_platform(app: App) -> None:
    async with app.test_api() as ctx:
        bot = fake_console_bot(ctx)
        event = fake_console_event()

        ctx.should_call_send(event, ConsoleMessage("Console"))
        async with ensure_context(bot, event) as api:
            await api.feedback(await api.get_platform())


@pytest.mark.anyio
async def test_api_reply_id(app: App) -> None:
    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event = fake_v11_event()
        event.reply = Reply(
            time=1000000,
            message_type="test",
            message_id=123,
            real_id=1,
            sender=Sender(card="", nickname="test", role="member"),
            message=V11Message(),
        )

        ctx.should_call_send(event, V11Message("123"))
        async with ensure_context(bot, event) as api:
            await api.feedback(await api.reply_id())


@respx.mock
@pytest.mark.anyio
@pytest.mark.usefixtures("app")
async def test_api_http_request() -> None:
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


@pytest.mark.anyio
async def test_api_native_send(app: App) -> None:
    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event = fake_v11_event()
        ctx.should_call_send(event, V11Message("123"), arg="test")
        async with ensure_context(bot, event) as api:
            await api.native_send("123", arg="test")
