import asyncio
import functools
import inspect
from typing import (
    Any,
    Awaitable,
    Callable,
    ClassVar,
    Coroutine,
    Iterable,
    Optional,
    Self,
    cast,
    overload,
)
from typing_extensions import TypeIs

from nonebot.adapters import Bot, Message, MessageSegment
from nonebot.log import logger
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


def export[**P, R](call: Callable[P, R]) -> Callable[P, R]:
    """将一个方法标记为导出函数"""
    setattr(call, INTERFACE_EXPORT_METHOD, True)
    return call


type Coro[T] = Coroutine[None, None, T]


def is_coroutine_callable(call: Callable[..., Any]) -> TypeIs[Callable[..., Coro[Any]]]:
    """检查 call 是否是一个 callable 协程函数"""
    if inspect.isroutine(call):
        return inspect.iscoroutinefunction(call)
    if inspect.isclass(call):
        return False
    func = getattr(call, "__call__", None)
    return inspect.iscoroutinefunction(func)


@overload
def debug_log[**P, R](call: Callable[P, Coro[R]]) -> Callable[P, Coro[R]]: ...


@overload
def debug_log[**P, R](call: Callable[P, R]) -> Callable[P, R]: ...


def debug_log[**P, R](call: Callable[P, Coro[R] | R]) -> Callable[P, Coro[R] | R]:
    if is_coroutine_callable(call):
        # 本来应该用 # pyright: ignore[reportRedeclaration]
        # 但是格式化后有点难绷，所以直接用了 # type: ignore
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:  # type: ignore
            logger.debug(f"{call.__name__}: args={args}, kwargs={kwargs}")
            return await cast(Callable[P, Coro[R]], call)(*args, **kwargs)

    else:

        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            logger.debug(f"{call.__name__}: args={args}, kwargs={kwargs}")
            return cast(Callable[P, R], call)(*args, **kwargs)

    return functools.update_wrapper(wrapper, call, assigned=WRAPPER_ASSIGNMENTS)


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
    error: Optional[Exception] = None
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
    return isinstance(message, (str, Message, MessageSegment, UniMessage, Segment))


async def as_unimsg(message: T_Message) -> UniMessage:
    if isinstance(message, MessageSegment):
        message = cast(type[Message], message.get_message_class())(message)
    if isinstance(message, (str, Segment)):
        message = UniMessage(message)
    elif isinstance(message, Message):
        message = await UniMessage.generate(message=message)

    return message


def _send_message(limit: int):
    class ReachLimit(Exception):
        def __init__(self, msg: str, count: int) -> None:
            self.msg, self.count = msg, count

    call_cnt: dict[int, int] = {}

    def clean_cnt(key: int):
        if key in call_cnt:
            del call_cnt[key]

    def send_message(
        session: Session,
        target: Optional[Target],
        message: T_Message,
    ) -> Awaitable[Receipt]:
        key = id(session)
        if key not in call_cnt:
            call_cnt[key] = 1
            asyncio.get_event_loop().call_later(60, clean_cnt, key)
        elif call_cnt[key] >= limit or call_cnt[key] < 0:
            call_cnt[key] = -1
            raise ReachLimit("消息发送触发次数限制", limit)
        else:
            call_cnt[key] += 1

        async def send_message_inner():
            msg = await as_unimsg(message)
            return await msg.send(target)

        return asyncio.create_task(send_message_inner())

    return send_message


send_message = _send_message(limit=6)


def send_forward_message(
    session: Session,
    target: Optional[Target],
    msgs: Iterable[T_Message],
) -> Awaitable[Receipt]:
    async def create_node(msg: T_Message) -> CustomNode:
        return CustomNode(
            uid="0",
            name="forward",
            content=await as_unimsg(msg),
        )

    async def send_forward_inner():
        nodes = await asyncio.gather(*[create_node(msg) for msg in msgs])
        return await send_message(
            session=session,
            target=target,
            message=Reference(nodes=nodes),
        )

    return asyncio.create_task(send_forward_inner())


def _export_manager():
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


export_manager = _export_manager()
