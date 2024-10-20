import asyncio
import functools
import inspect
from collections.abc import Callable, Coroutine, Generator
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Generic,
    ParamSpec,
    TypeVar,
    cast,
    get_type_hints,
    overload,
)

import nonebot
from nonebot.adapters import Adapter, Bot, Message, MessageSegment
from nonebot.utils import is_coroutine_callable
from nonebot_plugin_alconna.uniseg import Receipt, Segment, Target, UniMessage
from nonebot_plugin_session import Session
from tarina import generic_isinstance
from typing_extensions import Self

from ..typings import T_API_Result, T_Context, T_Message, is_message_t

if TYPE_CHECKING:
    from .help_doc import MethodDescription

INTERFACE_EXPORT_METHOD = "__export_method__"
"""接口方法上的 bool 类型变量，标识该方法是否为导出函数"""
INTERFACE_METHOD_DESCRIPTION = "__method_description__"
"""接口方法上的 weakref.RefrenceType 类型变量，弱引用该方法的描述"""

WRAPPER_ASSIGNMENTS = (
    *functools.WRAPPER_ASSIGNMENTS,
    INTERFACE_EXPORT_METHOD,
    INTERFACE_METHOD_DESCRIPTION,
)

_P = ParamSpec("_P")
_R = TypeVar("_R", contravariant=True)
_T = TypeVar("_T")


def export(call: Callable[_P, _R]) -> Callable[_P, _R]:
    """将一个方法标记为导出方法
    Args:
        call (Callable[P, R]): 待标记的方法
    Returns:
        Callable[P, R]: 标记为导出方法的方法
    """
    setattr(call, INTERFACE_EXPORT_METHOD, True)
    return call


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


class Coro(Coroutine[None, None, _T], Generic[_T]): ...


T_Args = tuple[Any, ...]
T_Kwargs = dict[str, Any]
BeforeWrapped = Callable[[T_Args, T_Kwargs], tuple[T_Args, T_Kwargs] | None]
AfterWrapped = Callable[[T_Args, T_Kwargs, Any], tuple[bool, Any]]


def make_wrapper(
    wrapped: Callable[_P, Coro[_R]] | Callable[_P, _R],
    before: BeforeWrapped | None = None,
    after: AfterWrapped | None = None,
) -> Callable[_P, Coro[_R]] | Callable[_P, _R]:
    """包装函数 `wrapped`, 在调用前执行 `before`, 在调用后执行 `after`

    Args:
        wrapped (Callable[P, R]): 被包装的函数
        before (BeforeWrapped | None, optional):
            在函数调用前执行的操作, 接收传入函数的参数 (args, kwargs),
            返回修改后的参数(可选). Defaults to None.
        after (AfterWrapped[R] | None, optional):
            在函数调用后执行的操作, 接收传入函数的参数和返回值 (args, kwargs, result),
            返回修改后的返回值(可选). Defaults to None.

    Returns:
        Callable[P, R]: 包装后的函数
    """

    call = wrapped
    before_calls: tuple[BeforeWrapped, ...] = (before,) if before else ()
    after_calls: tuple[AfterWrapped, ...] = (after,) if after else ()

    # 如果已经被包装过，提取原函数和对应的 _before/_after
    # before -> *_before -> call -> *_after -> after
    if wrapped_data := getattr(wrapped, "__exe_code_wrapped__", None):
        call, _before, _after = wrapped_data
        before_calls = (*before_calls, *_before)
        after_calls = (*_after, *after_calls)

    def call_before(args: T_Args, kwargs: T_Kwargs) -> tuple[T_Args, T_Kwargs]:
        for call in before_calls:
            if res := call(args, kwargs):
                args, kwargs = res
        return args, kwargs

    def call_after(args: T_Args, kwargs: T_Kwargs, result: Any) -> Any:
        for call in after_calls:
            mock, value = call(args, kwargs, result)
            if mock:
                result = value
        return result

    # 解析被包装函数的类型，创建 同步/异步 wrapper
    if is_coroutine_callable(call):

        async def wrapper_async(*args: Any, **kwargs: Any) -> Any:
            args, kwargs = call_before(args, kwargs)
            result = await cast(Callable[_P, Coro[_R]], call)(*args, **kwargs)
            return call_after(args, kwargs, result)

        wrapper = cast(Callable[_P, _R], wrapper_async)

    else:

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            args, kwargs = call_before(args, kwargs)
            result = cast(Callable[_P, _R], call)(*args, **kwargs)
            return call_after(args, kwargs, result)

    # 使用 functools.update_wrapper 更新 wrapper 上的各属性
    wrapper = functools.update_wrapper(wrapper, wrapped, assigned=WRAPPER_ASSIGNMENTS)
    # 保存本次包装的参数
    setattr(  # noqa: B010
        wrapper,
        "__exe_code_wrapped__",
        (call, before_calls, after_calls),
    )

    return wrapper


@overload
def debug_log(call: Callable[_P, Coro[_R]]) -> Callable[_P, Coro[_R]]: ...
@overload
def debug_log(call: Callable[_P, _R]) -> Callable[_P, _R]: ...


def debug_log(
    call: Callable[_P, Coro[_R]] | Callable[_P, _R],
) -> Callable[_P, Coro[_R]] | Callable[_P, _R]:
    """装饰一个函数，使其在被调用时输出 DEBUG 日志
    Args:
        call (Callable[P, R]): 被装饰的函数
    Returns:
        Callable[P, R]: 装饰后的函数
    """

    def before(args: T_Args, kwargs: T_Kwargs) -> None:
        nonebot.logger.debug(f"{call.__name__}: args={args!r}, kwargs={kwargs!r}")

    return make_wrapper(call, before)


def _check_args(
    call: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> None:
    """检查函数调用是否符合类型注解

    Args:
        call (Callable[..., Any]): 待调用的函数
        args (tuple[Any, ...]): 调用函数的参数 *args
        kwargs (dict[str, Any]): 调用函数的参数 **kwargs

    Raises:
        TypeError: 传入的参数无法正确调用函数
            / 无法解析函数类型注解
            / 函数参数不符合类型注解
    """
    arguments = inspect.signature(call).bind(*args, **kwargs).arguments
    arguments.pop("cls", None)
    arguments.pop("self", None)
    if not arguments:
        return

    annotations = get_type_hints(call)
    for name, value in arguments.items():
        annotation = annotations[name]
        if not generic_isinstance(value, annotation):
            from .help_doc import format_annotation

            raise TypeError(
                f"Invalid argument for param {name!r} of {call.__name__!r}: "
                f"expected {format_annotation(annotation)}, "
                f"got {format_annotation(type(value))}"
            )


@overload
def strict(call: Callable[_P, Coro[_R]]) -> Callable[_P, Coro[_R]]: ...
@overload
def strict(call: Callable[_P, _R]) -> Callable[_P, _R]: ...


def strict(
    call: Callable[_P, Coro[_R]] | Callable[_P, _R],
) -> Callable[_P, Coro[_R]] | Callable[_P, _R]:
    """装饰一个函数，使其在被调用时的传参严格符合参数类型注解
    Args:
        call (Callable[P, R]): 被装饰的函数
    Raises:
        TypeError: 参数没有添加必要的类型注解
    Returns:
        Callable[P, R]: 装饰后的函数。若没有需要检查的参数则返回原函数。
    """

    signature = inspect.signature(call)

    if not (set(signature.parameters.keys()) - {"cls", "self"}):
        # 没有需要检查的参数
        return call

    for name, param in signature.parameters.items():
        if name not in {"cls", "self"} and param.annotation is signature.empty:
            # 参数 {name} 未添加类型注解
            raise TypeError(
                f"Parameter {name!r} of "
                f"strict callable {call.__name__!r} is not typed"
            )

    def before(args: T_Args, kwargs: T_Kwargs) -> None:
        _check_args(call, args, kwargs)

    return make_wrapper(call, before)


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
