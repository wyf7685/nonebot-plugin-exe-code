# ruff: noqa: N806

from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal

from nonebot.adapters.console import Adapter, Bot, Message, MessageEvent, User
from nonebug.mixin.call_api import ApiContext
from nonebug.mixin.process import MatcherContext
from pydantic import create_model

from .common import fake_bot

if TYPE_CHECKING:
    from nonebot_plugin_session import Session


def fake_console_bot(ctx: ApiContext | MatcherContext, **kwargs: Any) -> Bot:
    return fake_bot(ctx, Adapter, Bot, **kwargs)


def fake_console_message_event(**field: Any) -> MessageEvent:
    _Fake = create_model("_Fake", __base__=MessageEvent)

    class FakeEvent(_Fake):
        time: datetime = datetime.now()  # noqa: DTZ005
        self_id: str = "pytest"
        post_type: Literal["message"] = "message"
        user: User = User("nonebug")
        message: Message = Message()

    return FakeEvent(**field)


def fake_console_event_session(bot: Bot) -> tuple[MessageEvent, "Session"]:
    from nonebot_plugin_session import extract_session

    event = fake_console_message_event()
    return event, extract_session(bot, event)
