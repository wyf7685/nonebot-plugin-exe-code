import itertools
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from nonebot.adapters.onebot.v11 import GroupMessageEvent as GroupMessageEventV11
    from nonebot.adapters.onebot.v11 import Message
    from nonebot.adapters.onebot.v11 import (
        PrivateMessageEvent as PrivateMessageEventV11,
    )
    from nonebot.adapters.qq import MessageCreateEvent as MessageCreateEvent


def _faker(gen: "itertools.count[int]"):
    def faker():
        return next(gen)

    return faker


fake_user_id = _faker(itertools.count(100))
fake_group_id = _faker(itertools.count(200))
fake_img_bytes = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```"
    b"\x00\x00\x00\x04\x00\x01\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82"
)


def fake_group_message_event_v11(**field) -> "GroupMessageEventV11":
    from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message
    from nonebot.adapters.onebot.v11.event import Sender
    from pydantic import create_model

    _Fake = create_model("_Fake", __base__=GroupMessageEvent)

    class FakeEvent(_Fake):
        time: int = 1000000
        self_id: int = 1
        post_type: Literal["message"] = "message"
        sub_type: str = "normal"
        user_id: int = 10
        message_type: Literal["group"] = "group"
        group_id: int = 10000
        message_id: int = 1
        message: Message = Message("test")
        raw_message: str = "test"
        font: int = 0
        sender: Sender = Sender(
            card="",
            nickname="test",
            role="member",
        )
        to_me: bool = False

    return FakeEvent(**field)


def fake_private_message_event_v11(**field) -> "PrivateMessageEventV11":
    from nonebot.adapters.onebot.v11 import Message, PrivateMessageEvent
    from nonebot.adapters.onebot.v11.event import Sender
    from pydantic import create_model

    _Fake = create_model("_Fake", __base__=PrivateMessageEvent)

    class FakeEvent(_Fake):
        time: int = 1000000
        self_id: int = 1
        post_type: Literal["message"] = "message"
        sub_type: str = "friend"
        user_id: int = 10
        message_type: Literal["private"] = "private"
        message_id: int = 1
        message: Message = Message("test")
        raw_message: str = "test"
        font: int = 0
        sender: Sender = Sender(nickname="test")
        to_me: bool = False

    return FakeEvent(**field)


def fake_group_exe_code(group_id: int, user_id: int, code: "str | Message"):
    from nonebot.adapters.onebot.v11 import MessageSegment

    event = fake_group_message_event_v11(
        group_id=group_id,
        user_id=user_id,
        message=MessageSegment.text("code ") + code,
    )
    return event


def fake_private_exe_code(user_id: int, code: str):
    from nonebot.adapters.onebot.v11 import MessageSegment

    event = fake_private_message_event_v11(
        user_id=user_id,
        message=MessageSegment.text("code ") + code,
    )
    return event
