from collections import UserString
from collections.abc import Awaitable, Callable
from typing import Any, Self, TypeGuard

from nonebot.adapters import Message, MessageSegment
from nonebot_plugin_alconna.uniseg import Segment, UniMessage
from tarina import generic_isinstance

type T_Context = dict[str, Any]
type T_Executor = Callable[[], Awaitable[object]]
type T_API_Result = dict[str, Any] | list[Any] | None
T_Message = str | Message | MessageSegment | UniMessage | Segment
T_ConstVar = str | bool | int | float | dict | list | None


class UserStr(UserString):
    __slots__ = ("__user_str_args__",)
    __user_str_args__: list[T_Message]

    def put_arg(self, msg: T_Message) -> Self:
        if not generic_isinstance(msg, T_Message):
            raise TypeError(
                f"unsupported operand type(s): 'UserStr' and {type(msg).__name__!r}"
            )

        if not hasattr(self, "__user_str_args__"):
            self.__user_str_args__ = []

        self.__user_str_args__.append(msg)
        return self

    __and__ = put_arg
    __matmul__ = put_arg

    def extract_args(self) -> list[T_Message]:
        return self.__user_str_args__.copy()


T_ForwardMsg = list[str] | list[T_Message] | list[UserStr] | list[T_Message | UserStr]


def is_message_t(message: Any) -> TypeGuard[T_Message]:
    return isinstance(message, T_Message)
