import asyncio

import pytest
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot.adapters.qq.models import MessageArk, MessageArkKv
from nonebug import App
from pytest_mock import MockerFixture

from tests.conftest import exe_code_qbot_id
from tests.fake import (
    ensure_context,
    fake_qq_bot,
    fake_qq_c2c_message_create_event,
    fake_v11_bot,
    fake_v11_event_session,
    fake_v11_private_message_event,
)

code_test_ob11_send_ark = """\
await api.ark_24("title", "desc", "prompt", "img", "link")
"""
expected_ark_24 = MessageArk(
    template_id=24,
    kv=[
        MessageArkKv(key="#TITLE#", value="title"),
        MessageArkKv(key="#METADESC#", value="desc"),
        MessageArkKv(key="#PROMPT#", value="prompt"),
        MessageArkKv(key="#IMG#", value="img"),
        MessageArkKv(key="#LINK#", value="link"),
    ],
)


@pytest.mark.asyncio
async def test_ob11_send_ark(app: App, mocker: MockerFixture):
    import uuid

    from nonebot.adapters.qq import MessageSegment as QQMS
    from nonebot.message import handle_event

    from nonebot_plugin_exe_code.context import Context

    mocker.patch("os.urandom", return_value=b"0" * 16)
    key = f"$ARK-{uuid.uuid4()}$"
    card = "JSON_DATA"

    async with app.test_api() as ctx:
        botV11 = fake_v11_bot(ctx, self_id="test-v11")
        botQQ = fake_qq_bot(ctx, self_id="test-qq")

        event_code, session = fake_v11_event_session(botV11)
        event_qq = fake_qq_c2c_message_create_event(content=key)
        event_v11 = fake_v11_private_message_event(
            user_id=exe_code_qbot_id,
            message=Message(MessageSegment.json(card)),
        )
        ctx.should_call_api(
            "send_msg",
            {
                "message_type": "private",
                "user_id": exe_code_qbot_id,
                "message": Message(key),
            },
            {"message_id": 1},
        )
        ctx.should_call_send(event_qq, QQMS.ark(expected_ark_24), bot=botQQ)
        ctx.should_call_send(event_code, Message(MessageSegment.json(card)))

        async def _test1():
            with ensure_context(botV11, event_code):
                await Context.execute(botV11, session, code_test_ob11_send_ark)

        async def _test2():
            await asyncio.sleep(0.01)
            await handle_event(botQQ, event_qq)

        async def _test3():
            await asyncio.sleep(0.02)
            await handle_event(botV11, event_v11)

        await asyncio.gather(_test1(), _test2(), _test3())


@pytest.mark.asyncio
async def test_ob11_send_ark_fail(app: App, mocker: MockerFixture):
    import uuid

    from nonebot.adapters.qq import MessageSegment as QQMS
    from nonebot.message import handle_event

    from nonebot_plugin_exe_code.context import Context

    mocker.patch("os.urandom", return_value=b"0" * 16)
    key = f"$ARK-{uuid.uuid4()}$"

    async with app.test_api() as ctx:
        botV11 = fake_v11_bot(ctx, self_id="test-v11")
        botQQ = fake_qq_bot(ctx, self_id="test-qq")

        event_code, session = fake_v11_event_session(botV11)
        event_qq = fake_qq_c2c_message_create_event(content=key)
        ctx.should_call_api(
            "send_msg",
            {
                "message_type": "private",
                "user_id": exe_code_qbot_id,
                "message": Message(key),
            },
            {"message_id": 1},
        )
        ctx.should_call_send(
            event_qq,
            QQMS.ark(expected_ark_24),
            bot=botQQ,
            exception=RuntimeError("test"),
        )

        async def _test1():
            with (
                ensure_context(botV11, event_code),
                pytest.raises(RuntimeError, match="test"),
            ):
                await Context.execute(botV11, session, code_test_ob11_send_ark)

        async def _test2():
            await asyncio.sleep(0.01)
            await handle_event(botQQ, event_qq)

        await asyncio.gather(_test1(), _test2())
