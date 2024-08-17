import contextlib
from typing_extensions import override

from ...constant import T_Context
from ..api import API as BaseAPI
from ..api import register_api
from ..help_doc import message_alia

with contextlib.suppress(ImportError):
    from nonebot.adapters.telegram import Adapter, Message, MessageSegment

    message_alia(Message, MessageSegment)

    @register_api(Adapter)
    class API(BaseAPI):
        @override
        def export_to(self, context: T_Context) -> None:
            super().export_to(context)
            context["Message"] = Message
            context["MessageSegment"] = MessageSegment
