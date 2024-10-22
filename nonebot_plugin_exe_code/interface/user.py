from typing import TYPE_CHECKING, ClassVar

from nonebot_plugin_alconna.uniseg import Receipt

from ..typings import T_Message
from .decorators import debug_log, strict
from .help_doc import descript
from .interface import Interface

if TYPE_CHECKING:
    from .api import API


class User[A: API](Interface):
    __parameters__ = (A,)
    __inst_name__: ClassVar[str] = "usr"
    __slots__ = ("api", "uid")

    api: A
    uid: str

    def __init__(self, api: A, uid: str) -> None:
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
