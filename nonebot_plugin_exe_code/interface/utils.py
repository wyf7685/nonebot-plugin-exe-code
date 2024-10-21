import asyncio
from collections.abc import Callable, Generator
from typing import TYPE_CHECKING, Any, ClassVar, cast

import nonebot
from nonebot.adapters import Adapter, Bot, Message, MessageSegment
from nonebot_plugin_alconna.uniseg import Receipt, Segment, Target, UniMessage
from nonebot_plugin_session import Session
from typing_extensions import Self

from ..typings import T_API_Result, T_Context, T_Message, is_message_t
from .decorators import INTERFACE_EXPORT_METHOD, INTERFACE_METHOD_DESCRIPTION, strict

if TYPE_CHECKING:
    from .help_doc import MethodDescription


def is_export_method(call: Callable[..., Any]) -> bool:
    """判断一个方法是否为导出函数
    Args:
        call (Callable[..., Any]): 待判断的方法
    Returns:
        bool: 该方法是否为导出函数
    """
    return getattr(call, INTERFACE_EXPORT_METHOD, False)


def get_method_description(call: Callable[..., Any]) -> "MethodDescription | None":
    if (ref := getattr(call, INTERFACE_METHOD_DESCRIPTION, None)) is None:
        return None
    if (desc := ref()) is None:
        raise RuntimeError("Fail to solve weak refrence")  # pragma: no cover
    return desc


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


async def as_unimsg(message: Any) -> UniMessage[Any]:
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


def as_unimsg_sync(message: Any) -> UniMessage[Any]:
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


def export_superuser() -> Generator[tuple[str, Any], Any, None]:
    yield from {"sudo": _Sudo()}.items()


_msg_cls_cache: dict[str, tuple[type[Message], type[MessageSegment]]] = {}


def _get_msg_cls(adapter: Adapter) -> tuple[type[Message], type[MessageSegment]]:
    adapter_name = adapter.get_name()
    if adapter_name in _msg_cls_cache:
        return _msg_cls_cache[adapter_name]

    msg = UniMessage.text("text").export_sync(adapter=adapter_name)
    return _msg_cls_cache.setdefault(adapter_name, (type(msg), msg.get_segment_class()))


@nonebot.get_driver().on_startup
async def _on_driver_startup() -> None:
    from .help_doc import message_alia

    for a in nonebot.get_adapters().values():
        message_alia(*_get_msg_cls(a))


def export_message(adapter: Adapter) -> Generator[tuple[str, Any], Any, None]:
    m, ms = _get_msg_cls(adapter)
    yield from {"Message": m, "MessageSegment": ms}.items()
