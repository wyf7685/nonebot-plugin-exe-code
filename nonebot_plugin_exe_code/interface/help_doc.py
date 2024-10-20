# ruff: noqa: S101

import inspect
import weakref
from collections.abc import Callable
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
from .utils import INTERFACE_METHOD_DESCRIPTION, Result, make_wrapper

if TYPE_CHECKING:
    from .interface import Interface

TI = TypeVar("TI", bound="Interface")
TP = ParamSpec("TP")
TR = TypeVar("TR")

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
class MethodDescription(Generic[TI, TP, TR]):
    inst_name: str
    call: Callable[Concatenate[TI, TP], TR]
    description: str
    parameters: dict[str, str] | None
    result: str | None
    ignore: set[str]

    def format(self) -> str:
        return DESCRIPTION_FORMAT.format(
            decl=func_declaration(self.call, self.ignore),
            desc=self.description,
            params=(
                "\n".join(f" - {k}: {v}" for k, v in self.parameters.items())
                if self.parameters
                else "无"
            ),
            res=self.result or "无",
        )


class MethodDescriptor(Generic[TI, TP, TR]):
    __name: str
    __desc: MethodDescription[TI, TP, TR]

    def __init__(self, desc: MethodDescription[TI, TP, TR]) -> None:
        self.__name = desc.call.__name__
        self.__desc = desc
        setattr(desc.call, INTERFACE_METHOD_DESCRIPTION, weakref.ref(desc))

    def __set_name__(self, owner: type[TI], name: str) -> None:
        self.__name = name
        self.__desc.inst_name = owner.__inst_name__

    def __make_wrapper(self, obj: TI) -> Callable[TP, TR]:
        def before(args: tuple, kwargs: dict) -> tuple[tuple, dict]:
            return (obj, *args), kwargs

        return cast(Callable[TP, TR], make_wrapper(self.__desc.call, before))

    @overload
    def __get__(self, obj: TI, objtype: type[TI]) -> Callable[TP, TR]: ...
    @overload
    def __get__(
        self, obj: None, objtype: type[TI]
    ) -> Callable[Concatenate[TI, TP], TR]: ...

    def __get__(
        self, obj: TI | None, objtype: type[TI]
    ) -> Callable[TP, TR] | Callable[Concatenate[TI, TP], TR]:
        return self.__desc.call if obj is None else self.__make_wrapper(obj)

    def __set__(self, obj: TI, value: Callable[Concatenate[TI, TP], TR]) -> NoReturn:
        raise AttributeError(f"attribute {self.__name!r} of {obj!r} is readonly")

    def __delete__(self, obj: TI) -> NoReturn:
        raise AttributeError(f"attribute {self.__name!r} of {obj!r} cannot be deleted")

    def __getattr__(self, __name: str) -> Any:
        return getattr(self.__desc.call, __name)


def descript(
    description: str,
    parameters: dict[str, str] | None,
    result: str | None = None,
    *,
    ignore: set[str] | None = None,
) -> Callable[[Callable[Concatenate[TI, TP], TR]], MethodDescriptor[TI, TP, TR]]:
    ignore = {"self", *(ignore or set())}

    def decorator(
        call: Callable[Concatenate[TI, TP], TR],
    ) -> MethodDescriptor[TI, TP, TR]:
        nonlocal result

        sig = inspect.signature(call)
        if parameters is not None:
            unused = set(parameters) - set(sig.parameters)
            assert not unused, f"方法 {call.__name__!r} 存在多余的描述: {unused!r}"
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

        return MethodDescriptor(
            MethodDescription(
                inst_name="[unbound]",
                call=call,
                description=description,
                parameters=parameters,
                result=result,
                ignore=ignore,
            )
        )

    return decorator
