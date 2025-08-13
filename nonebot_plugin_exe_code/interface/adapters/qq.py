import contextlib
from typing import override

from nonebot.adapters import Event

from ..api import API as BaseAPI

with contextlib.suppress(ImportError):
    from nonebot.adapters.qq import Adapter, Bot
    from nonebot.adapters.qq.event import MessageEvent

    class API(BaseAPI[Bot, MessageEvent], adapter=Adapter):
        __slots__ = ()

        @classmethod
        @override
        def _validate(cls, bot: Bot, event: Event) -> bool:
            return isinstance(bot, Bot) and isinstance(event, MessageEvent)

        @property
        @override
        def mid(self) -> str | int:
            return self.event.event_id or super().mid
