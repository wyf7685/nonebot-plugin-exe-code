# ruff: noqa: S101

import functools
import inspect
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Concatenate,
    Generic,
    NoReturn,
    ParamSpec,
    TypeVar,
    cast,
    overload,
)

from nonebot.adapters import Message, MessageSegment
from nonebot_plugin_alconna.uniseg import Receipt

from ..typings import T_ConstVar, T_ForwardMsg, T_Message
from .utils import INTERFACE_METHOD_DESCRIPTION, WRAPPER_ASSIGNMENTS, Result

if TYPE_CHECKING:
    from .interface import Interface

_T = TypeVar("_T", bound="Interface")
_P = ParamSpec("_P")
_R = TypeVar("_R")

DESCRIPTION_FORMAT = "{decl}\n* 描述: {desc}\n* 参数:\n{params}\n* 返回值:\n  {res}\n"
DESCRIPTION_RESULT_TYPE = "Result 对象，可通过属性名获取接口响应"
DESCRIPTION_RECEIPT_TYPE = "UniMessage 发送后返回的 Receipt 对象，用于操作对应消息"

EMPTY = inspect.Signature.empty
type_alias: dict[Any, str] = {
    Receipt: "Receipt",
    Result: "Result",
    T_ConstVar: "T_ConstVar",
    T_Message: "T_Message",
    T_ForwardMsg: "T_ForwardMsg",
    EMPTY: "Unkown",  # not supposed to appear in docs
}


def message_alia(m: type[Message], ms: type[MessageSegment], /) -> None:
    type_alias[m] = "Message"
    type_alias[ms] = "MessageSegment"


def format_annotation(t: type | str) -> str:
    if isinstance(t, str):
        return t
    if t in type_alias:
        return type_alias[t]
    return inspect.formatannotation(t)


def func_declaration(func: Callable[..., Any], ignore: set[str]) -> str:
    sig = inspect.signature(func)
    params = [
        f"{name}: {format_annotation(param.annotation)}"
        for name, param in sig.parameters.items()
        if name not in ignore
    ]
    result = format_annotation(sig.return_annotation)

    return f"{func.__name__}({', '.join(params)}) -> {result}"


@dataclass
class MethodDescription(Generic[_T, _P, _R]):
    inst_name: str
    func: Callable[Concatenate[_T, _P], _R]
    description: str
    parameters: dict[str, str] | None
    result: str | None
    ignore: set[str]

    def format(self) -> str:
        return DESCRIPTION_FORMAT.format(
            decl=func_declaration(self.func, self.ignore),
            desc=self.description,
            params=(
                "\n".join(f" - {k}: {v}" for k, v in self.parameters.items())
                if self.parameters
                else "无"
            ),
            res=self.result or "无",
        )


class _MethodDescriptor(Generic[_T, _P, _R]):
    name: str
    desc: MethodDescription[_T, _P, _R]

    def __init__(self, desc: MethodDescription[_T, _P, _R]) -> None:
        self.desc = desc
        setattr(desc.func, INTERFACE_METHOD_DESCRIPTION, desc)

    def __set_name__(self, owner: type[_T], name: str) -> None:
        self.name = name
        self.desc.inst_name = owner.__inst_name__

    def __make_wrapper(self, obj: _T) -> Callable[_P, _R]:
        if inspect.iscoroutinefunction(self.desc.func):

            async def wrapper_async(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                return await cast(
                    Callable[Concatenate[_T, _P], Coroutine[None, None, _R]],
                    self.desc.func,
                )(obj, *args, **kwargs)

            wrapper = cast(Callable[_P, _R], wrapper_async)
        else:

            def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                return self.desc.func(obj, *args, **kwargs)

        return functools.update_wrapper(
            wrapper=wrapper,
            wrapped=self.desc.func,
            assigned=WRAPPER_ASSIGNMENTS,
        )

    @overload
    def __get__(self, obj: _T, objtype: type[_T]) -> Callable[_P, _R]: ...
    @overload
    def __get__(
        self, obj: None, objtype: type[_T]
    ) -> Callable[Concatenate[_T, _P], _R]: ...

    def __get__(
        self, obj: _T | None, objtype: type[_T]
    ) -> Callable[_P, _R] | Callable[Concatenate[_T, _P], _R]:
        return self.desc.func if obj is None else self.__make_wrapper(obj)

    def __set__(self, obj: _T, value: Callable[Concatenate[_T, _P], _R]) -> NoReturn:
        raise AttributeError(f"attribute {self.name!r} of {obj!r} is readonly")

    def __delete__(self, obj: _T) -> NoReturn:
        raise AttributeError(f"attribute {self.name!r} of {obj!r} cannot be deleted")

    def __getattr__(self, __name: str) -> Any:
        return getattr(self.desc.func, __name)


def descript(
    description: str,
    parameters: dict[str, str] | None,
    result: str | None = None,
    *,
    ignore: set[str] | None = None,
) -> Callable[[Callable[Concatenate[_T, _P], _R]], _MethodDescriptor[_T, _P, _R]]:
    ignore = {"self", *(ignore or set())}

    def decorator(
        call: Callable[Concatenate[_T, _P], _R],
    ) -> _MethodDescriptor[_T, _P, _R]:
        nonlocal result

        sig = inspect.signature(call)
        if parameters is not None:
            for name, param in sig.parameters.items():
                if name in ignore:
                    continue
                text = f"方法 {call.__name__!r} 的参数 {name!r}"
                assert param.annotation is not EMPTY, f"{text} 未添加类型注释"
                assert name in parameters, f"{text} 未添加描述"

        ret = sig.return_annotation
        text = f"方法 {call.__name__!r} 的返回值"
        assert ret is not EMPTY, f"{text} 未添加类型注释"

        if result is None:
            if ret is Result:
                result = DESCRIPTION_RESULT_TYPE
            elif ret is Receipt:
                result = DESCRIPTION_RECEIPT_TYPE
            elif "return" not in ignore:
                assert ret is None, f"{text} 未添加描述"

        return _MethodDescriptor(
            MethodDescription(
                inst_name="[unbound]",
                func=call,
                description=description,
                parameters=parameters,
                result=result,
                ignore=ignore,
            )
        )

    return decorator
