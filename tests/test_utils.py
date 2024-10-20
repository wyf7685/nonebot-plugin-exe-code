from collections.abc import Awaitable, Callable, Iterable
from typing import Any

import pytest
from nonebot.utils import run_sync
from nonebug import App

from .fake.common import ensure_context
from .fake.onebot11 import fake_v11_bot, fake_v11_event_session


@pytest.mark.usefixtures("app")
def test_make_wrapper() -> None:
    from nonebot_plugin_exe_code.interface.utils import T_Args, T_Kwargs, make_wrapper

    before_called = after_called = False

    def func(*args: Any, **kwargs: Any) -> tuple[T_Args, T_Kwargs]:
        return args, kwargs

    def before(args: T_Args, kwargs: T_Kwargs) -> tuple[T_Args, T_Kwargs]:
        nonlocal before_called
        before_called = True
        return ((111, *args), {"aaa": 222, **kwargs})

    def after(args: T_Args, kwargs: T_Kwargs, result: Any) -> tuple[bool, Any]:
        nonlocal after_called
        after_called = True
        return True, (args, kwargs, result)

    result = make_wrapper(func, before, after)(333, bbb=444)
    expected = (
        (111, 333),
        {"aaa": 222, "bbb": 444},
        ((111, 333), {"aaa": 222, "bbb": 444}),
    )

    assert before_called
    assert after_called
    assert result == expected


@pytest.mark.usefixtures("app")
def test_strict() -> None:
    from nonebot_plugin_exe_code.interface.utils import strict

    with pytest.raises(TypeError, match="not typed"):

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

    class _Test:
        @strict
        def method(self) -> None: ...
        @classmethod
        @strict
        def classmethod_(cls) -> None: ...
        @staticmethod
        @strict
        def staticmethod_() -> None: ...

    assert not hasattr(_Test.method, "__wrapped__")
    assert not hasattr(_Test.classmethod_, "__wrapped__")
    assert not hasattr(_Test.staticmethod_, "__wrapped__")


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

    assert (UserStr("some string") @ "123" & "456").extract_args() == ["123", "456"]
    with pytest.raises(TypeError):
        _ = UserStr("some string") @ 123  # pyright: ignore[reportOperatorIssue]
