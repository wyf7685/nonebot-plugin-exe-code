import contextlib

from nonebot.adapters import Event
from typing_extensions import override

from ..api import API as BaseAPI
from ..api import register_api

with contextlib.suppress(ImportError):
    from nonebot.adapters.telegram import Adapter, Bot
    from nonebot.adapters.telegram.event import MessageEvent

    @register_api(Adapter)
    class API(BaseAPI[Bot, MessageEvent]):
        __slots__ = ()

        @classmethod
        @override
        def _validate(cls, bot: Bot, event: Event) -> bool:
            return isinstance(bot, Bot) and isinstance(event, MessageEvent)
