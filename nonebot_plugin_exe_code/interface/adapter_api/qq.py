import contextlib
from typing import Any

from typing_extensions import override

from ..api import API as BaseAPI
from ..api import register_api
from ..help_doc import descript
from ..utils import debug_log
from ._send_ark import SendArk

with contextlib.suppress(ImportError):
    from nonebot.adapters.qq import Adapter, Bot, Event, MessageSegment
    from nonebot.adapters.qq.models import MessageArk

    @register_api(Adapter)
    class API(SendArk, BaseAPI[Bot, Event]):
        @override
        async def _send_ark(self, ark: MessageArk) -> Any:
            return await self._native_send(MessageSegment.ark(ark))

        @descript(
            description="发送ark卡片",
            parameters=dict(ark="通过build_ark构建的ark结构体"),
        )
        @debug_log
        async def send_ark(self, ark: MessageArk) -> None:
            await self._send_ark(ark)
