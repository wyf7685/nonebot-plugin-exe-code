import contextlib
import functools
import inspect
from collections.abc import Callable, Coroutine
from typing import (
    TYPE_CHECKING,
    Any,
    Concatenate,
    NoReturn,
    Protocol,
    cast,
    get_overloads,
    get_type_hints,
    overload,
    runtime_checkable,
)

import nonebot
from nonebot.utils import is_coroutine_callable
from tarina import generic_isinstance

from ..exception import ParamMismatch

INTERFACE_EXPORT_METHOD = "__export_method__"
"""接口方法上的 bool 类型变量，标识该方法是否为导出函数"""
INTERFACE_METHOD_DESCRIPTION = "__method_description__"
"""接口方法上的 weakref.RefrenceType 类型变量，弱引用该方法的描述"""

WRAPPER_ASSIGNMENTS = (
    *functools.WRAPPER_ASSIGNMENTS,
    INTERFACE_EXPORT_METHOD,
    INTERFACE_METHOD_DESCRIPTION,
)


def export[**P, R](call: Callable[P, R]) -> Callable[P, R]:
    """将一个方法标记为导出方法
    Args:
        call (Callable[P, R]): 待标记的方法
    Returns:
        Callable[P, R]: 标记为导出方法的方法
    """
    setattr(call, INTERFACE_EXPORT_METHOD, True)
    return call


type Coro[T] = Coroutine[None, None, T]
type T_Args = tuple[Any, ...]
type T_Kwargs = dict[str, Any]
type BeforeWrapped = Callable[[T_Args, T_Kwargs], tuple[T_Args, T_Kwargs] | None]
type AfterWrapped = Callable[[T_Args, T_Kwargs, Any], tuple[bool, Any]]
type AnyCallable[**P, R] = Callable[P, Coro[R]] | Callable[P, R]


def make_wrapper[**P, R](
    wrapped: Callable[P, Coro[R]] | Callable[P, R],
    before: BeforeWrapped | None = None,
    after: AfterWrapped | None = None,
) -> Callable[P, Coro[R]] | Callable[P, R]:
    """包装函数 `wrapped`, 在调用前执行 `before`, 在调用后执行 `after`

    Args:
        wrapped (Callable[P, R]): 被包装的函数
        before (BeforeWrapped | None, optional):
            在函数调用前执行的操作, 接收传入函数的参数 (args, kwargs),
            返回修改后的参数(可选). Defaults to None.
        after (AfterWrapped[R] | None, optional):
            在函数调用后执行的操作, 接收传入函数的参数和返回值 (args, kwargs, result),
            返回修改后的返回值(可选). Defaults to None.

    Returns:
        Callable[P, R]: 包装后的函数
    """

    call = wrapped
    before_calls: tuple[BeforeWrapped, ...] = (before,) if before else ()
    after_calls: tuple[AfterWrapped, ...] = (after,) if after else ()

    # 如果已经被包装过，提取原函数和对应的 _before/_after
    # before -> *_before -> call -> *_after -> after
    if wrapped_data := getattr(wrapped, "__exe_code_wrapped__", None):
        call, _before, _after = wrapped_data
        before_calls = (*before_calls, *_before)
        after_calls = (*_after, *after_calls)

    def call_before(args: T_Args, kwargs: T_Kwargs) -> tuple[T_Args, T_Kwargs]:
        for call in before_calls:
            if res := call(args, kwargs):
                args, kwargs = res
        return args, kwargs

    def call_after(args: T_Args, kwargs: T_Kwargs, result: Any) -> Any:
        for call in after_calls:
            mock, value = call(args, kwargs, result)
            if mock:
                result = value
        return result

    # 解析被包装函数的类型，创建 同步/异步 wrapper
    if is_coroutine_callable(call):

        async def wrapper_async(*args: Any, **kwargs: Any) -> Any:
            args, kwargs = call_before(args, kwargs)
            result = await cast(Callable[P, Coro[R]], call)(*args, **kwargs)
            return call_after(args, kwargs, result)

        wrapper = cast(Callable[P, R], wrapper_async)

    else:

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            args, kwargs = call_before(args, kwargs)
            result = cast(Callable[P, R], call)(*args, **kwargs)
            return call_after(args, kwargs, result)

    # 使用 functools.update_wrapper 更新 wrapper 上的各属性
    wrapper = functools.update_wrapper(wrapper, wrapped, assigned=WRAPPER_ASSIGNMENTS)
    # 保存本次包装的参数
    setattr(  # noqa: B010
        wrapper,
        "__exe_code_wrapped__",
        (call, before_calls, after_calls),
    )

    return wrapper


@overload
def debug_log[**P, R](call: Callable[P, Coro[R]]) -> Callable[P, Coro[R]]: ...
@overload
def debug_log[**P, R](call: Callable[P, R]) -> Callable[P, R]: ...


def debug_log[**P, R](call: AnyCallable[P, R]) -> AnyCallable[P, R]:
    """装饰一个函数，使其在被调用时输出 DEBUG 日志
    Args:
        call (Callable[P, R]): 被装饰的函数
    Returns:
        Callable[P, R]: 装饰后的函数
    """

    def before(args: T_Args, kwargs: T_Kwargs) -> None:
        nonebot.logger.debug(f"{call.__name__}: args={args!r}, kwargs={kwargs!r}")

    return make_wrapper(call, before)


def _check_args(call: Callable[..., Any], args: T_Args, kwargs: T_Kwargs) -> None:
    """检查函数调用是否符合类型注解

    Args:
        call (Callable[..., Any]): 待调用的函数
        args (tuple[Any, ...]): 调用函数的参数 *args
        kwargs (dict[str, Any]): 调用函数的参数 **kwargs

    Raises:
        TypeError: 传入的参数无法正确调用函数
            / 无法解析函数类型注解
            / 函数参数不符合类型注解
    """
    arguments = inspect.signature(call).bind(*args, **kwargs).arguments
    arguments.pop("cls", None)
    arguments.pop("self", None)
    if not arguments:
        return

    annotations = get_type_hints(call)
    for name, value in arguments.items():
        annotation = annotations[name]
        if not generic_isinstance(value, annotation):
            from .help_doc import format_annotation

            raise TypeError(
                f"Invalid argument for param {name!r} of {call.__name__!r}: "
                f"expected {format_annotation(annotation)}, "
                f"got {format_annotation(type(value))}"
            )


@overload
def strict[**P, R](call: Callable[P, Coro[R]]) -> Callable[P, Coro[R]]: ...
@overload
def strict[**P, R](call: Callable[P, R]) -> Callable[P, R]: ...


def strict[**P, R](call: AnyCallable[P, R]) -> AnyCallable[P, R]:
    """装饰一个函数，使其在被调用时的传参严格符合参数类型注解
    Args:
        call (Callable[P, R]): 被装饰的函数
    Raises:
        TypeError: 参数没有添加必要的类型注解
    Returns:
        Callable[P, R]: 装饰后的函数。若没有需要检查的参数则返回原函数。
    """

    signature = inspect.signature(call)

    if not (set(signature.parameters.keys()) - {"cls", "self"}):
        # 没有需要检查的参数
        return call

    for name, param in signature.parameters.items():
        if name not in {"cls", "self"} and param.annotation is signature.empty:
            # 参数 {name} 未添加类型注解
            raise TypeError(
                f"Parameter {name!r} of strict callable {call.__name__!r} is not typed"
            )

    def before(args: T_Args, kwargs: T_Kwargs) -> None:
        _check_args(call, args, kwargs)

    return make_wrapper(call, before)


@runtime_checkable
class _DescriptorType[T, **P, R](Protocol):
    @overload
    def __get__(self, obj: T, objtype: type[T]) -> Callable[P, R]: ...
    @overload
    def __get__(
        self, obj: None, objtype: type[T]
    ) -> Callable[Concatenate[T, P], R]: ...
    def __set_name__(self, owner: type[T], name: str) -> None: ...


class Overload[T, **P, R]:
    def __init__(
        self, call: Callable[Concatenate[T, P], R] | _DescriptorType[T, P, R]
    ) -> None:
        self.__origin = call

    def __set_name__(self, owner: type[T], name: str) -> None:
        self.__name = name
        if _set_name := getattr(self.__origin, "__set_name__", None):
            _set_name(owner, name)

    def __find_overload(self, args: T_Args, kwargs: T_Kwargs) -> Callable[..., Any]:
        for call in self.__overloads:
            with contextlib.suppress(TypeError):
                _check_args(call, args, kwargs)
                return call
        raise ParamMismatch(f"未找到匹配的重载: {args=}, {kwargs=}")

    @overload
    def __get__(self, obj: T, objtype: type[T]) -> Callable[P, R]: ...
    @overload
    def __get__(
        self, obj: None, objtype: type[T]
    ) -> Callable[Concatenate[T, P], R]: ...

    def __get__(
        self, obj: T | None, objtype: type[T]
    ) -> Callable[P, R] | Callable[Concatenate[T, P], R]:
        call = self.__origin
        if _get := getattr(self.__origin, "__get__", None):
            call = _get(obj, objtype)

        if TYPE_CHECKING:
            call = cast(Callable[Concatenate[T, P], R], call)

        if not hasattr(self, "__overloads__"):
            self.__overloads = get_overloads(call)
            assert self.__overloads, "应提供至少一个函数重载"

        if is_coroutine_callable(call):

            async def wrapper_async(*args: Any, **kwargs: Any) -> Any:
                if obj is not None:
                    args = (obj, *args)
                return await self.__find_overload(args, kwargs)(*args, **kwargs)

            wrapper = cast(Callable[..., Any], wrapper_async)
        else:

            def wrapper(*args: Any, **kwargs: Any) -> Any:
                if obj is not None:
                    args = (obj, *args)
                return self.__find_overload(args, kwargs)(*args, **kwargs)

        return functools.update_wrapper(wrapper, call, assigned=WRAPPER_ASSIGNMENTS)

    def __set__(self, obj: T, value: Any) -> Any:
        raise AttributeError(f"attribute {self.__name!r} of {obj!r} is readonly")

    def __delete__(self, obj: T) -> NoReturn:
        raise AttributeError(f"attribute {self.__name!r} of {obj!r} cannot be deleted")

    def __getattr__(self, name: str, /) -> Any:
        return getattr(self.__origin, name)
