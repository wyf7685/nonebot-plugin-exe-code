import asyncio
import functools
import inspect
from collections.abc import Callable, Coroutine
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Generic,
    ParamSpec,
    TypeVar,
    cast,
    overload,
)

import nonebot
from nonebot.adapters import Adapter, Bot, Message, MessageSegment
from nonebot.utils import is_coroutine_callable
from nonebot_plugin_alconna.uniseg import Receipt, Segment, Target, UniMessage
from nonebot_plugin_session import Session
from typing_extensions import Self, TypeIs

from ..typings import T_API_Result, T_Context, T_Message, generic_check_isinstance

if TYPE_CHECKING:
    from .help_doc import MethodDescription

INTERFACE_EXPORT_METHOD = "__export_method__"
INTERFACE_METHOD_DESCRIPTION = "__method_description__"
WRAPPER_ASSIGNMENTS = (
    *functools.WRAPPER_ASSIGNMENTS,
    INTERFACE_EXPORT_METHOD,
    INTERFACE_METHOD_DESCRIPTION,
)

_P = ParamSpec("_P")
_R = TypeVar("_R")
_T = TypeVar("_T")


def export(call: Callable[_P, _R]) -> Callable[_P, _R]:
    """将一个方法标记为导出函数"""
    setattr(call, INTERFACE_EXPORT_METHOD, True)
    return call


def get_method_description(call: Callable[..., Any]) -> "MethodDescription | None":
    return getattr(call, INTERFACE_METHOD_DESCRIPTION, None)


class Coro(Coroutine[None, None, _T], Generic[_T]): ...


@overload
def debug_log(call: Callable[_P, Coro[_R]]) -> Callable[_P, Coro[_R]]: ...
@overload
def debug_log(call: Callable[_P, _R]) -> Callable[_P, _R]: ...


def debug_log(
    call: Callable[_P, Coro[_R]] | Callable[_P, _R],
) -> Callable[_P, Coro[_R]] | Callable[_P, _R]:
    if is_coroutine_callable(call):

        async def wrapper(  # pyright: ignore[reportRedeclaration]
            *args: _P.args, **kwargs: _P.kwargs
        ) -> _R:
            nonebot.logger.debug(f"{call.__name__}: args={args!r}, kwargs={kwargs!r}")
            return await cast(Callable[_P, Coro[_R]], call)(*args, **kwargs)

    else:

        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
            nonebot.logger.debug(f"{call.__name__}: args={args!r}, kwargs={kwargs!r}")
            return cast(Callable[_P, _R], call)(*args, **kwargs)

    return cast(
        Callable[_P, Coro[_R]] | Callable[_P, _R],
        functools.update_wrapper(wrapper, call, assigned=WRAPPER_ASSIGNMENTS),
    )


@overload
def strict(call: Callable[_P, Coro[_R]]) -> Callable[_P, Coro[_R]]: ...
@overload
def strict(call: Callable[_P, _R]) -> Callable[_P, _R]: ...


def strict(
    call: Callable[_P, Coro[_R]] | Callable[_P, _R],
) -> Callable[_P, Coro[_R]] | Callable[_P, _R]:
    sig = inspect.signature(call)
    params = sig.parameters.copy()
    params.pop("cls", None)
    params.pop("self", None)

    if any(param.annotation is sig.empty for param in params.values()):
        raise TypeError(f"Strict callable {call.__name__!r} is not fully typed")

    def check_args(args: tuple, kwargs: dict) -> None:
        arguments = sig.bind(*args, **kwargs).arguments
        for name, value in arguments.items():
            if name in {"cls", "self"}:
                continue
            annotation = sig.parameters[name].annotation
            if not generic_check_isinstance(value, annotation):
                from .help_doc import format_annotation

                raise TypeError(
                    f"Invalid argument for param {name!r} of {call.__name__!r}: "
                    f"expect {format_annotation(annotation)}, "
                    f"got {format_annotation(type(value))}"
                )

    if is_coroutine_callable(call):

        async def wrapper(  # pyright: ignore[reportRedeclaration]
            *args: _P.args, **kwargs: _P.kwargs
        ) -> _R:
            check_args(args, kwargs)
            return await cast(Callable[_P, Coro[_R]], call)(*args, **kwargs)

    else:

        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
            check_args(args, kwargs)
            return cast(Callable[_P, _R], call)(*args, **kwargs)

    return cast(
        Callable[_P, Coro[_R]] | Callable[_P, _R],
        functools.update_wrapper(wrapper, call, assigned=WRAPPER_ASSIGNMENTS),
    )


def is_export_method(call: Callable[..., Any]) -> bool:
    return getattr(call, INTERFACE_EXPORT_METHOD, False)


def is_super_user(bot: Bot, uin: str) -> bool:
    return (
        f"{bot.adapter.get_name().split(maxsplit=1)[0].lower()}:{uin}"
        in bot.config.superusers
        or uin in bot.config.superusers
    )


class Buffer:
    _user_buf: ClassVar[dict[str, Self]] = {}
    _buffer: str

    def __init__(self) -> None:
        self._buffer = ""

    @classmethod
    def get(cls, uin: str) -> Self:
        if uin not in cls._user_buf:
            cls._user_buf[uin] = cls()
        return cls._user_buf[uin]

    def write(self, text: str) -> None:
        self._buffer += str(text)

    def read(self) -> str:
        value, self._buffer = self._buffer, ""
        return value


class Result:
    error: Exception | None = None
    _data: T_API_Result

    def __init__(self, data: T_API_Result) -> None:
        self._data = data
        if isinstance(data, dict):
            self.error = data.get("error")
            for k, v in data.items():
                setattr(self, k, v)

    def __getitem__(self, key: str | int) -> Any:
        if isinstance(self._data, dict) and isinstance(key, str):
            return self._data[key]
        if isinstance(self._data, list) and isinstance(key, int):
            return self._data[key]
        if self._data is not None:
            raise KeyError(f"{key!r} 不能作为索引")
        raise TypeError("返回值 None 不支持索引操作")

    def __repr__(self) -> str:
        if self.error is not None:
            return f"<Result error={self.error!r}>"
        return f"<Result data={self._data!r}>"


def is_message_t(message: Any) -> TypeIs[T_Message]:
    return isinstance(message, T_Message)


async def as_unimsg(message: Any) -> UniMessage:
    if not is_message_t(message):
        message = str(message)
    if isinstance(message, MessageSegment):
        message = cast(type[Message], message.get_message_class())(message)
    if isinstance(message, str):
        message = UniMessage.text(message)
    if isinstance(message, Segment):
        message = UniMessage(message)
    elif isinstance(message, Message):
        message = await UniMessage.generate(message=message)

    return message


def as_unimsg_sync(message: Any) -> UniMessage:
    if not is_message_t(message):
        message = str(message)
    if isinstance(message, MessageSegment):
        message = cast(type[Message], message.get_message_class())(message)
    if isinstance(message, str):
        message = UniMessage.text(message)
    if isinstance(message, Segment):
        message = UniMessage(message)
    elif isinstance(message, Message):
        message = UniMessage.generate_sync(message=message)

    return message


async def as_msg(message: Any) -> Message:
    if not is_message_t(message):
        message = str(message)

    if isinstance(message, str | Segment):
        message = UniMessage(message)
    if isinstance(message, UniMessage):
        message = await message.export()
    if isinstance(message, MessageSegment):
        message = cast(type[Message], message.get_message_class())(message)

    return message


class ReachLimit(Exception):  # noqa: N818
    limit: int = 6

    def __init__(self, msg: str) -> None:
        self.msg = msg


def _send_message():  # noqa: ANN202
    call_cnt: dict[int, int] = {}

    def clean_cnt(key: int) -> None:  # pragma: no cover
        if key in call_cnt:
            del call_cnt[key]

    async def send_message(
        session: Session,
        target: Target | None,
        message: T_Message,
    ) -> Receipt:
        key = id(session)
        if key not in call_cnt:
            call_cnt[key] = 1
            asyncio.get_event_loop().call_later(60, clean_cnt, key)
        elif call_cnt[key] >= ReachLimit.limit or call_cnt[key] < 0:
            call_cnt[key] = -1
            raise ReachLimit("消息发送触发次数限制")
        else:
            call_cnt[key] += 1

        msg = await as_unimsg(message)
        return await msg.send(target)

    return send_message


send_message = _send_message()


class _Sudo:
    def __init__(self) -> None:
        from ..config import config
        from ..context import Context

        self.__config = config
        self.__Context = Context

    def set_usr(self, x: Any) -> bool:
        (s.remove if (x := str(x)) in (s := self.__config.user) else s.add)(x)
        return x in s

    def set_grp(self, x: Any) -> bool:
        (s.remove if (x := str(x)) in (s := self.__config.group) else s.add)(x)
        return x in s

    @strict
    def ctxd(self, uin: int | str) -> T_Context:
        return self.__Context.get_context(str(uin)).ctx

    @strict
    def ctx(self, uin: int | str) -> Any:
        ctx = self.ctxd(uin)

        return type(
            "_ContextProxy",
            (object,),
            {
                "__getattr__": lambda _, *args: dict.__getitem__(ctx, *args),
                "__setattr__": lambda _, *args: dict.__setitem__(ctx, *args),
                "__delattr__": lambda _, *args: dict.__delitem__(ctx, *args),
                "keys": lambda _: dict.keys(ctx),
            },
        )()


def export_superuser() -> dict[str, Any]:
    return {"sudo": _Sudo()}


@functools.cache
def _get_msg_cls(adapter: Adapter) -> tuple[type[Message], type[MessageSegment]]:
    msg = UniMessage.text("text").export_sync(adapter=adapter.get_name())
    return type(msg), msg.get_segment_class()


@nonebot.get_driver().on_startup
async def _on_driver_startup() -> None:
    from .help_doc import message_alia

    for a in nonebot.get_adapters().values():
        message_alia(*_get_msg_cls(a))


def export_message(adapter: Adapter) -> dict[str, Any]:
    m, ms = _get_msg_cls(adapter)
    return {"Message": m, "MessageSegment": ms}
