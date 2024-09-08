import contextlib

from ..api import API as BaseAPI
from ..api import register_api

with contextlib.suppress(ImportError):
    from nonebot.adapters.satori import Adapter

    @register_api(Adapter)
    class API(BaseAPI):
        pass
