import asyncio
import functools
from collections.abc import Callable, Coroutine, Iterable
from typing import Any, ClassVar, Generic, ParamSpec, TypeVar, cast, overload
from typing_extensions import Self, TypeIs

from nonebot.adapters import Bot, Message, MessageSegment
from nonebot.log import logger
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
    call: Callable[P, Coro[R]] | Callable[P, R]
) -> Callable[P, Coro[R]] | Callable[P, R]:
    if is_coroutine_callable(call):
        call = cast(Callable[P, Coro[R]], call)

        async def wrapper(  # pyright: ignore[reportRedeclaration]
            *args: P.args, **kwargs: P.kwargs
        ) -> R:
            logger.debug(f"{call.__name__}: args={args}, kwargs={kwargs}")
            return await call(*args, **kwargs)

    else:
        call = cast(Callable[P, R], call)

        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            logger.debug(f"{call.__name__}: args={args}, kwargs={kwargs}")
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
        assert isinstance(text, str)
        self._buffer += text

    def read(self) -> str:
        value, self._buffer = self._buffer, ""
        return value


class Result:
    error: Exception | None = None
    _data: T_API_Result

    def __init__(self, data: T_API_Result):
        self._data = data
        if isinstance(data, dict):
            self.error = data.get("error")
            for k, v in data.items():
                setattr(self, k, v)

    def __getitem__(self, key: str | int) -> Any:
        if isinstance(self._data, dict) and isinstance(key, str):
            return self._data[key]
        elif isinstance(self._data, list) and isinstance(key, int):
            return self._data[key]
        elif self._data is not None:
            raise KeyError(f"{key!r} 不能作为索引")
        else:
            raise TypeError("返回值 None 不支持索引操作")

    def __repr__(self) -> str:
        if self.error is not None:
            return f"<Result error={self.error!r}>"
        return f"<Result data={self._data!r}>"


def is_message_t(message: Any) -> TypeIs[T_Message]:
    return isinstance(message, T_Message)


async def as_unimsg(message: T_Message) -> UniMessage:
    if isinstance(message, MessageSegment):
        message = cast(type[Message], message.get_message_class())(message)
    if isinstance(message, str | Segment):
        message = UniMessage(message)
    elif isinstance(message, Message):
        message = await UniMessage.generate(message=message)

    return message


class ReachLimit(Exception):
    limit: int = 6

    def __init__(self, msg: str) -> None:
        self.msg = msg


def _send_message():
    call_cnt: dict[int, int] = {}

    def clean_cnt(key: int):  # pragma: no cover
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


def _export_superuser():
    def f(s: set[str], x: str):
        return (s.remove if x in s else s.add)(x) or x in s

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
