import contextlib

from ..api import API as BaseAPI
from ..api import register_api

with contextlib.suppress(ImportError):
    from nonebot.adapters.telegram import Adapter, Bot, Event

    @register_api(Adapter)
    class API(BaseAPI[Bot, Event]):
        pass  # wtf
