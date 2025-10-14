from collections.abc import Awaitable, Callable
from typing import Any

import anyio
import pytest
from nonebug import App

from .fake.onebot11 import ensure_v11_api


@pytest.mark.anyio
async def test_as_unimsg(app: App) -> None:
    from nonebot.adapters.onebot.v11 import MessageSegment as V11Seg
    from nonebot_plugin_alconna.uniseg import At, UniMessage

    from nonebot_plugin_exe_code.interface.utils import as_unimsg

    async with app.test_api() as ctx, ensure_v11_api(ctx):
        # fmt: off
        assert await as_unimsg("1234") == UniMessage.text("1234")
        assert await as_unimsg(1234) == UniMessage.text("1234")
        assert await as_unimsg([1234]) == UniMessage.text("[1234]")
        assert await as_unimsg(V11Seg.at(1234)) == UniMessage.at("1234")
        assert await as_unimsg(V11Seg.at(123) + V11Seg.text("456")) == UniMessage.at("123").text("456")  # noqa: E501
        assert await as_unimsg(At("user", "123")) == UniMessage.at("123")
        assert await as_unimsg(UniMessage("12345")) == UniMessage("12345")


@pytest.mark.anyio
async def test_as_msg(app: App) -> None:
    from nonebot.adapters import Message
    from nonebot.adapters.onebot.v11 import Message as V11Msg
    from nonebot.adapters.onebot.v11 import MessageSegment as V11Seg
    from nonebot_plugin_alconna.uniseg import At, UniMessage

    from nonebot_plugin_exe_code.interface.utils import as_msg

    async def test_convert(call: Callable[[Any], Awaitable[Message]]) -> None:
        # fmt: off
        assert await call("1234") == V11Msg("1234")
        assert await call(1234) == V11Msg("1234")
        assert await call([1234]) == V11Msg("[1234]")
        assert await call(V11Seg.at(1234)) == V11Msg(V11Seg.at(1234))
        assert await call(V11Seg.at(123) + V11Seg.text("456")) == V11Seg.at(123) + V11Seg.text("456")  # noqa: E501
        assert await call(At("user", "123")) == V11Msg(V11Seg.at(123))
        assert await call(UniMessage("12345")) == V11Msg("12345")

    async with app.test_api() as ctx, ensure_v11_api(ctx):
        await test_convert(as_msg)


@pytest.mark.anyio
@pytest.mark.usefixtures("app")
async def test_driver_startup() -> None:
    from nonebot_plugin_exe_code.interface.utils import _on_driver_startup

    await _on_driver_startup()


@pytest.mark.usefixtures("app")
def test_user_str() -> None:
    from nonebot_plugin_exe_code.typings import UserStr

    assert (UserStr("some string") @ "123" & "456").extract_args() == ["123", "456"]
    with pytest.raises(TypeError):
        _ = UserStr("some string") @ 123  # pyright: ignore[reportOperatorIssue]


@pytest.mark.anyio
async def test_call_later() -> None:
    from nonebot_plugin_exe_code.interface.utils import call_later

    called: bool = False

    async def callback() -> None:
        nonlocal called
        called = True

    call_later(0.01, callback)
    await anyio.sleep(0.03)
    assert called
