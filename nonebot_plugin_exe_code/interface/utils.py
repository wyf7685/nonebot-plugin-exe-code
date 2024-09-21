import asyncio
import functools
from collections.abc import Callable, Coroutine, Iterable
from typing import Any, ClassVar, Generic, ParamSpec, TypeVar, cast, overload

import nonebot
from nonebot.adapters import Adapter, Bot, Message, MessageSegment
from nonebot.internal.matcher import current_bot
from nonebot.utils import is_coroutine_callable
from nonebot_plugin_alconna.uniseg import (
    CustomNode,
    Receipt,
    Reference,
    Segment,
    Target,
    UniMessage,
)
from nonebot_plugin_session import Session
from typing_extensions import Self, TypeIs

from ..constant import (
    INTERFACE_EXPORT_METHOD,
    INTERFACE_METHOD_DESCRIPTION,
    T_API_Result,
    T_Context,
    T_Message,
)

WRAPPER_ASSIGNMENTS = (
    *functools.WRAPPER_ASSIGNMENTS,
    INTERFACE_EXPORT_METHOD,
    INTERFACE_METHOD_DESCRIPTION,
)

P = ParamSpec("P")
R = TypeVar("R")
T = TypeVar("T")


def export(call: Callable[P, R]) -> Callable[P, R]:
    """将一个方法标记为导出函数"""
    setattr(call, INTERFACE_EXPORT_METHOD, True)
    return call


class Coro(Coroutine[None, None, T], Generic[T]): ...


@overload
def debug_log(call: Callable[P, Coro[R]]) -> Callable[P, Coro[R]]: ...


@overload
def debug_log(call: Callable[P, R]) -> Callable[P, R]: ...


def debug_log(
    call: Callable[P, Coro[R]] | Callable[P, R],
) -> Callable[P, Coro[R]] | Callable[P, R]:
    if is_coroutine_callable(call):
        call = cast(Callable[P, Coro[R]], call)

        async def wrapper(  # pyright: ignore[reportRedeclaration]
            *args: P.args, **kwargs: P.kwargs
        ) -> R:
            nonebot.logger.debug(f"{call.__name__}: args={args!r}, kwargs={kwargs!r}")
            return await call(*args, **kwargs)

    else:
        call = cast(Callable[P, R], call)

        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            nonebot.logger.debug(f"{call.__name__}: args={args!r}, kwargs={kwargs!r}")
            return call(*args, **kwargs)

    return cast(
        Callable[P, Coro[R]] | Callable[P, R],
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
    if isinstance(message, str | Segment):
        message = UniMessage(message)
    elif isinstance(message, Message):
        message = await UniMessage.generate(message=message)

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


async def send_forward_message(
    session: Session,
    target: Target | None,
    msgs: Iterable[T_Message],
) -> Receipt:
    async def create_node(msg: T_Message) -> CustomNode:
        return CustomNode(
            uid="0",
            name="forward",
            content=await as_unimsg(msg),
        )

    nodes = await asyncio.gather(*[create_node(msg) for msg in msgs])
    return await send_message(
        session=session,
        target=target,
        message=Reference(nodes=nodes),
    )


def _export_superuser() -> Callable[[T_Context], None]:
    def f(s: set[str], x: str) -> bool:
        return (s.remove if x in s else s.add)(x) or (x in s)

    def set_usr(x: Any) -> bool:
        from ..config import config

        return f(config.user, str(x))

    def set_grp(x: Any) -> bool:
        from ..config import config

        return f(config.group, str(x))

    def export_manager(ctx: T_Context) -> None:
        from ..context import Context

        ctx["get_ctx"] = Context.get_context
        ctx["set_usr"] = set_usr
        ctx["set_grp"] = set_grp

    return export_manager


export_superuser = _export_superuser()


def _export_message() -> Callable[[T_Context], None]:
    def get_msg_cls(adapter: Adapter) -> tuple[type[Message], type[MessageSegment]]:
        msg = UniMessage.text("text").export_sync(adapter=adapter.get_name())
        return type(msg), msg.get_segment_class()

    @nonebot.get_driver().on_startup
    async def _() -> None:
        from .help_doc import message_alia

        for a in nonebot.get_adapters().values():
            message_alia(*get_msg_cls(a))

    def export_message(context: T_Context) -> None:
        context["Message"], context["MessageSegment"] = get_msg_cls(
            current_bot.get().adapter
        )

    return export_message


export_message = _export_message()
