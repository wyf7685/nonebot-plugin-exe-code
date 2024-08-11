import contextlib
from typing import Any
from typing_extensions import override

from ...constant import T_Context
from ..api import API as BaseAPI
from ..api import register_api
from ..help_doc import descript, message_alia
from ..utils import debug_log
from ._send_ark import SendArk

with contextlib.suppress(ImportError):
    from nonebot.adapters.qq import Adapter, Message, MessageSegment
    from nonebot.adapters.qq.models import MessageArk

    message_alia(Message, MessageSegment)

    @register_api(Adapter)
    class API(SendArk, BaseAPI):
        @override
        async def _send_ark(self, ark: MessageArk) -> Any:  # pragma: no cover
            return await self._native_send(MessageSegment.ark(ark))

        @descript(
            description="发送ark卡片",
            parameters=dict(ark="通过build_ark构建的ark结构体"),
        )
        @debug_log
        async def send_ark(self, ark: MessageArk) -> None:  # pragma: no cover
            await self._send_ark(ark)

        @override
        def export_to(self, context: T_Context) -> None:
            super().export_to(context)
            context["Message"] = Message
            context["MessageSegment"] = MessageSegment
