# ruff: noqa: S101

import base64
from contextlib import AsyncExitStack
from typing import Any

import pytest
from nonebot.adapters.onebot.v11.event import Reply, Sender
from nonebot.adapters.onebot.v11.message import Message, MessageSegment
from nonebot.dependencies import Dependent
from nonebot.exception import SkippedException
from nonebot.internal.matcher import Matcher
from nonebot.internal.params import DependsInner
from nonebug import App

from tests.fake import (
    ensure_context,
    fake_img_bytes,
    fake_user_id,
    fake_v11_bot,
    fake_v11_group_message_event,
)


def parse_handler_dependent(depends: DependsInner) -> Dependent[Any]:
    assert depends.dependency is not None
    return Dependent[Any].parse(
        call=depends.dependency,
        allow_types=Matcher.HANDLER_PARAM_TYPES,
    )


code_test_extract_code = (
    "print(" + MessageSegment.at(111) + ")\nprint(" + MessageSegment.image(b"") + ")\n"
)


@pytest.mark.asyncio
async def test_extract_code(app: App) -> None:
    from nonebot_plugin_exe_code.matchers.depends import _extract_code

    user_id = fake_user_id()
    img_url = "http://localhost/image.png"
    dependent = parse_handler_dependent(_extract_code())
    msg = Message(
        [
            MessageSegment.text("code print("),
            MessageSegment.at(user_id),
            MessageSegment.text(")\nprint("),
            MessageSegment("image", {"file": "image.png", "url": img_url}),
            MessageSegment.text(")"),
        ]
    )
    expected = f'print(UserStr("{user_id}"))\nprint("{img_url}")'

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event = fake_v11_group_message_event(message=msg)
        state = {}
        stack = AsyncExitStack()

        with ensure_context(bot, event):
            result = await dependent(bot=bot, event=event, state=state, stack=stack)
            assert result == expected


@pytest.mark.asyncio
async def test_extract_code_fail(app: App) -> None:
    from nonebot_plugin_exe_code.matchers.depends import _extract_code

    dependent = parse_handler_dependent(_extract_code())
    msg = Message(
        [
            MessageSegment.at(fake_user_id()),
            MessageSegment.text("code print(123)"),
        ]
    )
    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event = fake_v11_group_message_event(message=msg)
        state = {}
        stack = AsyncExitStack()

        with ensure_context(bot, event), pytest.raises(SkippedException):
            await dependent(bot=bot, event=event, state=state, stack=stack)


@pytest.mark.asyncio
async def test_event_image_1(app: App) -> None:
    from nonebot_plugin_alconna.uniseg import Image

    from nonebot_plugin_exe_code.matchers.depends import _event_image

    dependent = parse_handler_dependent(_event_image())
    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event = fake_v11_group_message_event(
            message=Message(
                [
                    MessageSegment.reply(1),
                    MessageSegment.text("getimg"),
                ]
            ),
            reply=Reply(
                time=1000000,
                message_type="test",
                message_id=1,
                real_id=1,
                sender=Sender(
                    card="",
                    nickname="test",
                    role="member",
                ),
                message=Message(
                    [
                        MessageSegment.at(fake_user_id()),
                        MessageSegment.image(fake_img_bytes),
                        MessageSegment.text("Other text"),
                    ]
                ),
            ).model_dump(),
        )
        state = {}
        stack = AsyncExitStack()
        expected = Image(id="base64://" + base64.b64encode(fake_img_bytes).decode())
        with ensure_context(bot, event):
            result = await dependent(bot=bot, event=event, state=state, stack=stack)
            assert result == expected


@pytest.mark.asyncio
async def test_event_image_2(app: App) -> None:
    from nonebot_plugin_alconna.uniseg import Image

    from nonebot_plugin_exe_code.matchers.depends import _event_image

    dependent = parse_handler_dependent(_event_image())
    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event = fake_v11_group_message_event(
            message=Message(
                [
                    MessageSegment.reply(1),
                    MessageSegment.text("getimg"),
                    MessageSegment.image(fake_img_bytes),
                ]
            ),
        )
        state = {}
        stack = AsyncExitStack()
        expected = Image(id="base64://" + base64.b64encode(fake_img_bytes).decode())
        with ensure_context(bot, event):
            result = await dependent(bot=bot, event=event, state=state, stack=stack)
            assert result == expected


@pytest.mark.asyncio
async def test_event_image_3(app: App) -> None:
    from nonebot_plugin_alconna.uniseg import Image

    from nonebot_plugin_exe_code.matchers.depends import _event_image

    dependent = parse_handler_dependent(_event_image())
    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event = fake_v11_group_message_event(
            message=Message(
                [
                    MessageSegment.image(b"\0\0\0"),
                    MessageSegment.image(fake_img_bytes),
                ]
            ),
        )
        state = {}
        stack = AsyncExitStack()
        expected = Image(id="base64://" + base64.b64encode(b"\0\0\0").decode())
        with ensure_context(bot, event):
            result = await dependent(bot=bot, event=event, state=state, stack=stack)
            assert result == expected


@pytest.mark.asyncio
async def test_event_image_fail(app: App) -> None:
    from nonebot_plugin_exe_code.matchers.depends import _event_image

    dependent = parse_handler_dependent(_event_image())
    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event = fake_v11_group_message_event(
            message=Message([MessageSegment.text("No image")]),
        )
        state = {}
        stack = AsyncExitStack()
        with ensure_context(bot, event), pytest.raises(SkippedException):
            await dependent(bot=bot, event=event, state=state, stack=stack)


@pytest.mark.asyncio
async def test_event_reply(app: App) -> None:
    from nonebot_plugin_alconna.uniseg import Reply as AlcReply

    from nonebot_plugin_exe_code.matchers.depends import _event_reply

    dependent = parse_handler_dependent(_event_reply())
    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        reply_msg = Message([MessageSegment.text("Other text")])
        reply_obj = Reply(
            time=1000000,
            message_type="test",
            message_id=1,
            real_id=1,
            sender=Sender(
                card="",
                nickname="test",
                role="member",
            ),
            message=reply_msg,
        )
        event = fake_v11_group_message_event(
            message=Message(
                [
                    MessageSegment.reply(1),
                    MessageSegment.text("Some text"),
                ]
            ),
            reply=reply_obj.model_dump(),
        )
        state = {}
        stack = AsyncExitStack()
        expected = AlcReply(str(reply_obj.message_id), reply_msg, reply_obj)
        with ensure_context(bot, event):
            result = await dependent(bot=bot, event=event, state=state, stack=stack)
            assert result == expected


@pytest.mark.asyncio
async def test_event_reply_fail(app: App) -> None:
    from nonebot_plugin_exe_code.matchers.depends import _event_reply

    dependent = parse_handler_dependent(_event_reply())
    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event = fake_v11_group_message_event(
            message=Message([MessageSegment.text("Some text")]),
        )
        state = {}
        stack = AsyncExitStack()
        with ensure_context(bot, event), pytest.raises(SkippedException):
            await dependent(bot=bot, event=event, state=state, stack=stack)


@pytest.mark.asyncio
async def test_event_reply_message_1(app: App) -> None:
    from nonebot_plugin_exe_code.matchers.depends import _event_reply_message

    dependent = parse_handler_dependent(_event_reply_message())
    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        reply_msg = Message([MessageSegment.text("Other text")])
        reply_obj = Reply(
            time=1000000,
            message_type="test",
            message_id=1,
            real_id=1,
            sender=Sender(
                card="",
                nickname="test",
                role="member",
            ),
            message=reply_msg,
        )
        event = fake_v11_group_message_event(
            message=Message(
                [
                    MessageSegment.reply(1),
                    MessageSegment.text("Some text"),
                ]
            ),
            reply=reply_obj.model_dump(),
        )
        state = {}
        stack = AsyncExitStack()
        with ensure_context(bot, event):
            result = await dependent(bot=bot, event=event, state=state, stack=stack)
            assert result == reply_msg


@pytest.mark.asyncio
async def test_event_reply_message_2(app: App) -> None:
    from nonebot_plugin_exe_code.matchers.depends import _event_reply_message

    dependent = parse_handler_dependent(_event_reply_message())
    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        reply_msg = Message([MessageSegment.text("Other text")])
        event = fake_v11_group_message_event(
            message=Message(
                [
                    MessageSegment.reply(1),
                    MessageSegment.text("Some text"),
                ]
            ),
        )
        event.reply = Reply(
            time=1000000,
            message_type="test",
            message_id=1,
            real_id=1,
            sender=Sender(
                card="",
                nickname="test",
                role="member",
            ),
            message=reply_msg,
        )
        event.reply.message = (
            reply_msg.extract_plain_text()
        )  # pyright:ignore[reportAttributeAccessIssue]
        state = {}
        stack = AsyncExitStack()
        with ensure_context(bot, event):
            result = await dependent(bot=bot, event=event, state=state, stack=stack)
            assert result == reply_msg


@pytest.mark.asyncio
async def test_event_reply_message_fail_1(app: App) -> None:
    from nonebot_plugin_exe_code.matchers.depends import _event_reply_message

    dependent = parse_handler_dependent(_event_reply_message())
    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event = fake_v11_group_message_event(
            message=Message(
                [
                    MessageSegment.reply(1),
                    MessageSegment.text("Some text"),
                ]
            ),
        )
        state = {}
        stack = AsyncExitStack()
        with ensure_context(bot, event), pytest.raises(SkippedException):
            await dependent(bot=bot, event=event, state=state, stack=stack)


@pytest.mark.asyncio
async def test_event_reply_message_fail_2(app: App) -> None:
    from nonebot_plugin_exe_code.matchers.depends import _event_reply_message

    dependent = parse_handler_dependent(_event_reply_message())
    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        reply_obj = Reply(
            time=1000000,
            message_type="test",
            message_id=1,
            real_id=1,
            sender=Sender(
                card="",
                nickname="test",
                role="member",
            ),
            message=Message(),
        )
        event = fake_v11_group_message_event(
            message=Message(
                [
                    MessageSegment.reply(1),
                    MessageSegment.text("Some text"),
                ]
            ),
            reply=reply_obj.model_dump(),
        )
        state = {}
        stack = AsyncExitStack()
        with ensure_context(bot, event), pytest.raises(SkippedException):
            await dependent(bot=bot, event=event, state=state, stack=stack)
