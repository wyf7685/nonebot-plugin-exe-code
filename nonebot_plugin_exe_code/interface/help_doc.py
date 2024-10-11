# ruff: noqa: S101

import functools
import inspect
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Concatenate, Generic, ParamSpec, TypeVar, overload

from nonebot.adapters import Message, MessageSegment
from nonebot_plugin_alconna.uniseg import Receipt

from ..constant import (
    DESCRIPTION_FORMAT,
    DESCRIPTION_RECEIPT_TYPE,
    DESCRIPTION_RESULT_TYPE,
    INTERFACE_METHOD_DESCRIPTION,
)
from ..typings import T_ConstVar, T_ForwardMsg, T_Message
from .utils import WRAPPER_ASSIGNMENTS, Result

EMPTY = inspect.Signature.empty
T = TypeVar("T")
P = ParamSpec("P")
R = TypeVar("R")

type_alias: dict[Any, str] = {
    Receipt: "Receipt",
    Result: "Result",
    T_ConstVar: "T_ConstVar",
    T_Message: "T_Message",
    T_ForwardMsg: "T_ForwardMsg",
    EMPTY: "Unkown",  # not supposed to appear in docs
}


def message_alia(m: type[Message], ms: type[MessageSegment]) -> None:
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
class FuncDescription:
    inst_name: str
    description: str
    parameters: dict[str, str] | None
    result: str | None
    ignore: set[str]
    func: Callable

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


class _FuncDescriptor(Generic[T, P, R]):
    wrapped: Callable[Concatenate[T, P], R]
    description: FuncDescription
    __method_description__: FuncDescription

    def __init__(
        self, call: Callable[Concatenate[T, P], R], desc: FuncDescription
    ) -> None:
        self.wrapped = call
        self.description = desc
        setattr(call, INTERFACE_METHOD_DESCRIPTION, desc)

    @overload
    def __get__(self, obj: T, objtype: type[T]) -> Callable[P, R]: ...
    @overload
    def __get__(
        self, obj: None, objtype: type[T]
    ) -> Callable[Concatenate[T, P], R]: ...

    def __get__(
        self, obj: T | None, objtype: type[T]
    ) -> Callable[P, R] | Callable[Concatenate[T, P], R]:
        inst_name = getattr(objtype, "__inst_name__", objtype.__name__.lower())
        self.description.inst_name = inst_name
        setattr(
            self.wrapped,
            INTERFACE_METHOD_DESCRIPTION,
            self.description,
        )

        if obj is None:
            return self.wrapped

        return functools.update_wrapper(
            functools.partial(self.wrapped, obj),
            self.wrapped,
            assigned=WRAPPER_ASSIGNMENTS,
        )

    def __getattr__(self, __name: str) -> Any:
        return getattr(self.wrapped, __name)


def descript(
    description: str,
    parameters: dict[str, str] | None,
    result: str | None = None,
    *,
    ignore: set[str] | None = None,
) -> Callable[[Callable[Concatenate[T, P], R]], _FuncDescriptor[T, P, R]]:
    ignore = {"self", *(ignore or set())}

    def decorator(
        call: Callable[Concatenate[T, P], R],
    ) -> _FuncDescriptor[T, P, R]:
        nonlocal result

        sig = inspect.signature(call)
        if parameters is not None:
            for name, param in sig.parameters.items():
                if name == "self" or name in ignore:
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

        desc = FuncDescription(
            inst_name="unkown",
            description=description,
            parameters=parameters,
            result=result,
            ignore=ignore,
            func=call,
        )
        return _FuncDescriptor(call, desc)

    return decorator
