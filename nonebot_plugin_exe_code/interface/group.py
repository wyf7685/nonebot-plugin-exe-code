from typing import TYPE_CHECKING, ClassVar

from nonebot_plugin_alconna.uniseg import Receipt

from ..constant import T_ForwardMsg, T_Message
from .help_doc import descript
from .interface import Interface
from .utils import debug_log

if TYPE_CHECKING:  # pragma: no cover
    from .api import API


class Group(Interface):
    __inst_name__: ClassVar[str] = "grp"
    api: "API"
    uid: str

    def __init__(self, api: "API", uid: str) -> None:
        super().__init__()
        self.api = api
        self.uid = uid

    @descript(
        description="向群聊发送消息",
        parameters=dict(msg="需要发送的消息"),
    )
    @debug_log
    async def send(self, msg: T_Message) -> Receipt:
        return await self.api.send_grp(self.uid, msg)

    @descript(
        description="向群聊发送合并转发消息",
        parameters=dict(msgs="需要发送的消息列表"),
    )
    @debug_log
    async def send_fwd(self, msgs: T_ForwardMsg) -> Receipt:
        return await self.api.send_grp_fwd(self.uid, msgs)

    def __repr__(self):
        return f"{self.__class__.__name__}(group_id={self.uid})"
