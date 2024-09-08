import contextlib

from ..api import API as BaseAPI
from ..api import register_api
from ..help_doc import message_alia

with contextlib.suppress(ImportError):
    from nonebot.adapters.telegram import Adapter, Message, MessageSegment

    message_alia(Message, MessageSegment)

    @register_api(Adapter)
    class API(BaseAPI):
        pass
