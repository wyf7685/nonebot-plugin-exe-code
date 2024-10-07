# ruff: noqa: S101

import inspect
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, ParamSpec, TypeVar

from nonebot.adapters import Message, MessageSegment
from nonebot_plugin_alconna.uniseg import Receipt

from ..constant import (
    DESCRIPTION_FORMAT,
    DESCRIPTION_RECEIPT_TYPE,
    DESCRIPTION_RESULT_TYPE,
    INTERFACE_METHOD_DESCRIPTION,
    T_ConstVar,
    T_ForwardMsg,
    T_Message,
)
from .utils import Result

EMPTY = inspect.Signature.empty
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
    description: str
    parameters: dict[str, str] | None
    result: str | None
    ignore: set[str]

    def format(self, func: Callable[..., Any]) -> str:
        return DESCRIPTION_FORMAT.format(
            decl=func_declaration(func, self.ignore),
            desc=self.description,
            params=(
                "\n".join(f" - {k}: {v}" for k, v in self.parameters.items())
                if self.parameters
                else "无"
            ),
            res=self.result or "无",
        )


def descript(
    description: str,
    parameters: dict[str, str] | None,
    result: str | None = None,
    *,
    ignore: set[str] | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    ignore = {"self", *(ignore or set())}

    def decorator(call: Callable[P, R]) -> Callable[P, R]:
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

        setattr(
            call,
            INTERFACE_METHOD_DESCRIPTION,
            FuncDescription(description, parameters, result, ignore),
        )
        return call

    return decorator
