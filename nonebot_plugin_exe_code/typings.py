import contextlib
from collections.abc import Callable, Coroutine
from typing import Any, get_args, get_origin

from nonebot.adapters import Message, MessageSegment
from nonebot.typing import origin_is_union
from nonebot.utils import generic_check_issubclass
from nonebot_plugin_alconna.uniseg import Segment, UniMessage


def generic_check_isinstance(value: Any, annotation: Any) -> bool:
    if annotation is Any:
        return True
    if annotation is float:
        return isinstance(value, int | float)
    if generic_check_issubclass(type(value), annotation):
        return True

    origin = get_origin(annotation)

    with contextlib.suppress(TypeError):
        if isinstance(value, (origin, annotation)):  # noqa: UP038
            return True

    if origin_is_union(origin):
        for type_ in get_args(annotation):
            if generic_check_isinstance(value, type_):
                return True

    return False


T_Context = dict[str, Any]
T_Executor = Callable[[], Coroutine[None, None, Any]]
T_API_Result = dict[str, Any] | list[Any] | None
T_Message = str | Message | MessageSegment | UniMessage | Segment
T_ConstVar = str | bool | int | float | dict | list | None


class UserStr(str):
    __slots__ = ("__user_str_args__",)
    __user_str_args__: list[T_Message]

    def __matmul__(self, msg: T_Message) -> "UserStr":
        if not generic_check_isinstance(msg, T_Message):
            raise TypeError(
                "unsupported operand type(s) for @: "
                f"'UserStr' and {type(msg).__name__!r}"
            )

        if not hasattr(self, "__user_str_args__"):
            self.__user_str_args__ = []

        self.__user_str_args__.append(msg)
        return self

    def extract_args(self) -> list[T_Message]:
        return self.__user_str_args__.copy()


T_ForwardMsg = list[T_Message | UserStr]
