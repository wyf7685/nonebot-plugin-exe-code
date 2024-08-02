import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from types import UnionType
from typing import Any

from nonebot.adapters import Message, MessageSegment
from nonebot_plugin_alconna.uniseg import Receipt

from ..constant import (
    DESCRIPTION_FORMAT,
    DESCRIPTION_RECEIPT_TYPE,
    DESCRIPTION_RESULT_TYPE,
    INTERFACE_METHOD_DESCRIPTION,
    T_ForwardMsg,
    T_Message,
    T_OptConstVar,
)
from .utils import Result

EMPTY = inspect.Signature.empty


type_alias: dict[type | UnionType, str] = {
    Receipt: "Receipt",
    Result: "Result",
    T_Message: "T_Message",
    T_ForwardMsg: "T_ForwardMsg",
    T_OptConstVar: "Optional[T_ConstVar]",
    EMPTY: "Unkown",  # not supposed to appear in docs
}


def message_alia(M: type[Message], MS: type[MessageSegment]) -> None:
    type_alias[M] = "Message"
    type_alias[MS] = "MessageSegment"


def _type_string(t: type | str) -> str:
    if isinstance(t, str):
        return t
    elif t in type_alias:
        return type_alias[t]
    return inspect.formatannotation(t)


def func_declaration(func: Callable[..., Any], ignore: set[str]) -> str:
    sig = inspect.signature(func)
    params = [
        f"{name}: {_type_string(param.annotation)}"
        for name, param in sig.parameters.items()
        if name not in ignore
    ]
    result = _type_string(sig.return_annotation)

    return f"{func.__name__}({', '.join(params)}) -> {result}"


@dataclass
class FuncDescription:
    description: str
    parameters: dict[str, str] | None
    result: str | None
    ignore: set[str]

    def format(self, func: Callable[..., Any]):
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


# fmt: off
def descript[**P, R](
    description: str,
    parameters: dict[str, str] | None,
    result: str | None = None,
    *,
    ignore: set[str] | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    # fmt: on
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
        if origin := getattr(ret, "__origin__", None):
            args: tuple[type, ...] = getattr(ret, "__args__")
            if origin is Awaitable:
                ret = args[0]

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
