from collections.abc import Iterable
from typing import Any, overload

import pytest
from nonebot.utils import is_coroutine_callable


@pytest.mark.usefixtures("app")
def test_make_wrapper() -> None:
    from nonebot_plugin_exe_code.interface.decorators import (
        T_Args,
        T_Kwargs,
        make_wrapper,
    )

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
    from nonebot_plugin_exe_code.interface.decorators import strict

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


@pytest.mark.anyio
@pytest.mark.usefixtures("app")
async def test_overload() -> None:
    from nonebot_plugin_exe_code.interface.decorators import Overload

    class _Test:
        def __init__(self) -> None:
            self.mark = 0

        @overload
        def test1(self, foo: int) -> None:
            assert isinstance(foo, int)
            self.mark |= 1 << 0

        @overload
        def test1(self, foo: str) -> None:
            assert isinstance(foo, str)
            self.mark |= 1 << 1

        @Overload
        def test1(self, foo: int | str) -> None: ...

        @overload
        async def test2(self, bar: int) -> None:
            assert isinstance(bar, int)
            self.mark |= 1 << 2

        @overload
        async def test2(self, bar: str) -> None:
            assert isinstance(bar, str)
            self.mark |= 1 << 3

        @Overload
        async def test2(self, bar: int | str) -> None: ...

        @Overload
        def test3(self) -> None: ...

    test = _Test()
    assert not is_coroutine_callable(test.test1)
    assert is_coroutine_callable(test.test2)

    test.test1(123)
    test.test1("abc")
    await test.test2(123)
    await test.test2("abc")

    assert test.mark == 0b1111

    with pytest.raises(TypeError, match="未找到匹配的重载"):
        test.test1([])  # type: ignore[reportCallIssue,reportArgumentType]

    with pytest.raises(AssertionError, match="应提供至少一个函数重载"):
        test.test3()

    with pytest.raises(AttributeError):
        test.test1 = None  # type: ignore[reportAttributeAccessIssue]

    with pytest.raises(AttributeError):
        del test.test1
