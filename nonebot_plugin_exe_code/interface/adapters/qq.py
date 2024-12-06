import contextlib
from typing import override

from nonebot.adapters import Event

from ..api import API as BaseAPI
from ..api import register_api

with contextlib.suppress(ImportError):
    from nonebot.adapters.qq import Adapter, Bot
    from nonebot.adapters.qq.event import MessageEvent

    @register_api(Adapter)
    class API(BaseAPI[Bot, MessageEvent]):
        __slots__ = ()

        @classmethod
        @override
        def _validate(cls, bot: Bot, event: Event) -> bool:
            return isinstance(bot, Bot) and isinstance(event, MessageEvent)
