import contextlib
from typing import Any

from nonebot.adapters import Event
from typing_extensions import override

from ..api import API as BaseAPI
from ..api import register_api
from ..help_doc import descript
from ..utils import debug_log, strict
from ._send_ark import SendArk

with contextlib.suppress(ImportError):
    from nonebot.adapters.qq import Adapter, Bot, MessageSegment
    from nonebot.adapters.qq.event import MessageEvent
    from nonebot.adapters.qq.models import MessageArk

    @register_api(Adapter)
    class API(SendArk, BaseAPI[Bot, MessageEvent]):
        __slots__ = ()

        @classmethod
        @override
        def _validate(cls, bot: Bot, event: Event) -> bool:
            return isinstance(bot, Bot) and isinstance(event, MessageEvent)

        @override
        async def _send_ark(self, ark: MessageArk) -> Any:
            return await self.native_send(MessageSegment.ark(ark))

        @descript(
            description="发送ark卡片",
            parameters=dict(ark="通过build_ark构建的ark结构体"),
        )
        @debug_log
        @strict
        async def send_ark(self, ark: MessageArk) -> None:
            await self._send_ark(ark)
