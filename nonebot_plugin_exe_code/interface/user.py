from typing import TYPE_CHECKING, ClassVar, Generic, TypeVar

from nonebot_plugin_alconna.uniseg import Receipt

from ..typings import T_Message
from .help_doc import descript
from .interface import Interface
from .utils import debug_log, strict

if TYPE_CHECKING:
    from .api import API

_A = TypeVar("_A", bound="API")


class User(Generic[_A], Interface):
    __inst_name__: ClassVar[str] = "usr"
    __slots__ = ("api", "uid")

    api: _A
    uid: str

    def __init__(self, api: _A, uid: str) -> None:
        super().__init__()
        self.api = api
        self.uid = uid

    @descript(
        description="向用户发送私聊消息",
        parameters=dict(msg="需要发送的消息"),
    )
    @strict
    @debug_log
    async def send(self, msg: T_Message) -> Receipt:
        return await self.api.send_prv(self.uid, msg)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} user_id={self.uid}>"
