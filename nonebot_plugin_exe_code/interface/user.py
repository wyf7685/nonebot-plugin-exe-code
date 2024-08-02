from collections.abc import Awaitable
from typing import TYPE_CHECKING, ClassVar

from nonebot_plugin_alconna.uniseg import Receipt

from ..constant import T_ForwardMsg, T_Message
from .help_doc import descript
from .interface import Interface
from .utils import debug_log

if TYPE_CHECKING:
    from .api import API


class User(Interface):
    __inst_name__: ClassVar[str] = "usr"
    api: "API"
    uid: str

    def __init__(self, api: "API", uid: str) -> None:
        super().__init__()
        self.api = api
        self.uid = uid

    @descript(
        description="向用户发送私聊消息",
        parameters=dict(msg="需要发送的消息"),
    )
    @debug_log
    def send(self, msg: T_Message) -> Awaitable[Receipt]:
        return self.api.send_prv(self.uid, msg)

    @descript(
        description="向用户发送私聊合并转发消息",
        parameters=dict(msgs="需要发送的消息列表"),
    )
    @debug_log
    def send_fwd(self, msgs: T_ForwardMsg) -> Awaitable[Receipt]:
        return self.api.send_prv_fwd(self.uid, msgs)

    def __repr__(self):
        return f"{self.__class__.__name__}(user_id={self.uid})"
