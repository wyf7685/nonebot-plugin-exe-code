from datetime import datetime
from typing import Any, Literal

from nonebot.adapters.console import Adapter, Bot, Message, MessageEvent
from nonebug.mixin.call_api import ApiContext
from nonebug.mixin.process import MatcherContext
from nonechat.model import Channel, Robot, User
from pydantic import Field, create_model

from .common import fake_bot, fake_message_id


def fake_console_bot(ctx: ApiContext | MatcherContext, **kwargs: Any) -> Bot:
    return fake_bot(ctx, Adapter, Bot, self_id=Robot("robot", "🤖"), **kwargs)


def fake_console_message_event(**field: Any) -> MessageEvent:
    class FakeEvent(create_model("_Fake", __base__=MessageEvent)):
        time: datetime = Field(default_factory=datetime.now)
        self_id: str = "robot"
        post_type: Literal["message"] = "message"
        user: User = User("nonebug")
        channel: Channel = Channel("test_channel", "Test Channel")
        message_id: str = str(fake_message_id())
        message: Message = Message()
        to_me: bool = False

    return FakeEvent(**field)


def fake_console_event() -> MessageEvent:
    return fake_console_message_event()
