from collections.abc import Awaitable, Callable, Iterable
from typing import Any

import pytest
from nonebot.utils import run_sync
from nonebug import App

from .fake import ensure_context, fake_v11_bot, fake_v11_event_session


@pytest.mark.usefixtures("app")
def test_strict() -> None:
    from nonebot_plugin_exe_code.interface.utils import strict

    with pytest.raises(TypeError, match="not fully typed"):

        @strict
        def _test_no_annotation(arg) -> None: ...  # noqa: ANN001

    @strict
    def _test_1(arg1: Any, arg2: str, arg3: int) -> None: ...

    assert _test_1(..., "123", 456) is None
    with pytest.raises(TypeError):
        _test_1(..., 123, "456")  # pyright: ignore[reportArgumentType]

    @strict
    def _test_2(arg: str | dict | set) -> None: ...

    assert _test_2("string") is None
    assert _test_2({}) is None
    assert _test_2({...}) is None
    with pytest.raises(TypeError):
        _test_2(arg=123)  # pyright: ignore[reportArgumentType]

    @strict
    def _test_3(arg: Iterable) -> None: ...

    assert _test_3(["123"]) is None
    assert _test_3("123") is None
    with pytest.raises(TypeError):
        _test_3(123)  # pyright: ignore[reportArgumentType]


@pytest.mark.asyncio
async def test_as_unimsg(app: App) -> None:
    from nonebot.adapters.onebot.v11 import MessageSegment as v11MS
    from nonebot_plugin_alconna.uniseg import At, UniMessage

    from nonebot_plugin_exe_code.interface.utils import as_unimsg, as_unimsg_sync

    async def test_convert(call: Callable[[Any], Awaitable[UniMessage]]) -> None:
        assert await call("1234") == UniMessage.text("1234")
        assert await call(1234) == UniMessage.text("1234")
        assert await call([1234]) == UniMessage.text("[1234]")
        assert await call(v11MS.at(1234)) == UniMessage.at("1234")
        assert await call(v11MS.at(123) + "456") == UniMessage.at("123").text("456")
        assert await call(At("user", "123")) == UniMessage.at("123")
        assert await call(UniMessage("12345")) == UniMessage("12345")

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot)
        with ensure_context(bot, event):
            await test_convert(as_unimsg)
            await test_convert(run_sync(as_unimsg_sync))


@pytest.mark.asyncio
async def test_as_msg(app: App) -> None:
    from nonebot.adapters import Message
    from nonebot.adapters.onebot.v11 import Message as v11Message
    from nonebot.adapters.onebot.v11 import MessageSegment as v11MS
    from nonebot_plugin_alconna.uniseg import At, UniMessage

    from nonebot_plugin_exe_code.interface.utils import as_msg

    async def test_convert(call: Callable[[Any], Awaitable[Message]]) -> None:
        assert await call("1234") == v11Message("1234")
        assert await call(1234) == v11Message("1234")
        assert await call([1234]) == v11Message("[1234]")
        assert await call(v11MS.at(1234)) == v11Message(v11MS.at(1234))
        assert await call(v11MS.at(123) + "456") == v11MS.at(123) + "456"
        assert await call(At("user", "123")) == v11Message(v11MS.at(123))
        assert await call(UniMessage("12345")) == v11Message("12345")

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot)
        with ensure_context(bot, event):
            await test_convert(as_msg)


@pytest.mark.asyncio
@pytest.mark.usefixtures("app")
async def test_driver_startup() -> None:
    from nonebot_plugin_exe_code.interface.utils import _on_driver_startup

    await _on_driver_startup()


@pytest.mark.usefixtures("app")
def test_user_str() -> None:
    from nonebot_plugin_exe_code.typings import UserStr

    assert (UserStr("some string") @ "123").extract_args() == ["123"]
    with pytest.raises(TypeError):
        _ = UserStr("some string") @ 123  # pyright: ignore[reportOperatorIssue]
