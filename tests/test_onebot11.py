# ruff: noqa: N806, N814

import asyncio

import pytest
from nonebot.adapters.onebot.v11 import ActionFailed, Message, MessageSegment
from nonebot.adapters.qq.models import MessageArk, MessageArkKv
from nonebug import App
from pytest_mock import MockerFixture

from tests.conftest import exe_code_group, exe_code_qbot_id
from tests.fake import (
    ensure_context,
    fake_group_id,
    fake_qq_bot,
    fake_qq_c2c_message_create_event,
    fake_v11_bot,
    fake_v11_event_session,
    fake_v11_private_message_event,
)

code_test_ob11_img_summary = """\
await api.img_summary("test")
"""


@pytest.mark.asyncio
async def test_ob11_img_summary(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    url = "http://localhost:8080/image.png"
    expected = Message(MessageSegment.image(url))
    expected[0].data["summary"] = "test"

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, session = fake_v11_event_session(bot, group_id=exe_code_group)
        with ensure_context(bot, event), pytest.raises(ValueError, match="无效 url"):
            await Context.execute(bot, event, code_test_ob11_img_summary)
        Context.get_context(session).set_value("gurl", url)
        ctx.should_call_send(event, expected)
        with ensure_context(bot, event):
            await Context.execute(bot, event, code_test_ob11_img_summary)


code_test_ob11_recall = """\
await recall(1)
"""


@pytest.mark.asyncio
async def test_ob11_recall(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot, group_id=exe_code_group)
        ctx.should_call_api("delete_msg", {"message_id": 1}, {})
        with ensure_context(bot, event):
            await Context.execute(bot, event, code_test_ob11_recall)


code_test_ob11_get_msg = """\
print(await get_msg(1))
"""


@pytest.mark.asyncio
async def test_ob11_get_msg(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot, group_id=exe_code_group)
        ctx.should_call_api(
            "get_msg",
            {"message_id": 1},
            {"raw_message": "123"},
        )
        ctx.should_call_send(event, Message("123"))
        with ensure_context(bot, event):
            await Context.execute(bot, event, code_test_ob11_get_msg)


code_test_ob11_get_fwd = """\
print((await get_fwd(1))[0])
"""


@pytest.mark.asyncio
async def test_ob11_get_fwd(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot, group_id=exe_code_group)
        ctx.should_call_api(
            "get_forward_msg",
            {"message_id": 1},
            {"messages": [{"raw_message": "123"}]},
        )
        ctx.should_call_send(event, Message("123"))
        with ensure_context(bot, event):
            await Context.execute(bot, event, code_test_ob11_get_fwd)


code_test_ob11_exception_1 = """\
res = await api.not_an_action(arg=123)
raise res.error
"""


@pytest.mark.asyncio
async def test_ob11_exception_1(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot, group_id=exe_code_group)
        ctx.should_call_api("not_an_action", {"arg": 123}, exception=ActionFailed())
        with ensure_context(bot, event), pytest.raises(ActionFailed):
            await Context.execute(bot, event, code_test_ob11_exception_1)


code_test_ob11_exception_2 = """\
print(await api.not_an_action(arg=123))
"""


@pytest.mark.asyncio
async def test_ob11_exception_2(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot, group_id=exe_code_group)
        ctx.should_call_api("not_an_action", {"arg": 123}, exception=Exception())
        ctx.should_call_send(event, Message("<Result error=Exception()>"))
        with ensure_context(bot, event):
            await Context.execute(bot, event, code_test_ob11_exception_2)


code_test_ob11_exception_3 = """\
try:
    await api.not_an_action(arg=123, raise_text="TEST")
except Exception as err:
    print(repr(err))
"""


@pytest.mark.asyncio
async def test_ob11_exception_3(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot, group_id=exe_code_group)
        ctx.should_call_api("not_an_action", {"arg": 123}, exception=Exception())
        ctx.should_call_send(event, Message("ActionFailed(msg='TEST')"))
        with ensure_context(bot, event):
            await Context.execute(bot, event, code_test_ob11_exception_3)


code_test_ob11_exception_4 = """\
print(api.__not_an_attr__)
"""


@pytest.mark.asyncio
async def test_ob11_exception_4(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot, group_id=exe_code_group)
        with ensure_context(bot, event), pytest.raises(AttributeError):
            await Context.execute(bot, event, code_test_ob11_exception_4)


code_test_ob11_call_api_1 = """\
res = await api.test_action(arg="ping")
print(res)
print(res[0])
"""


@pytest.mark.asyncio
async def test_ob11_call_api_1(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot, group_id=exe_code_group)
        ctx.should_call_api("test_action", {"arg": "ping"}, result=["pong"])
        ctx.should_call_send(
            event,
            Message(MessageSegment.text("<Result data=['pong']>\npong")),
        )
        with ensure_context(bot, event):
            await Context.execute(bot, event, code_test_ob11_call_api_1)


code_test_ob11_call_api_2 = """\
res = await api.test_action(arg="ping")
print(res["key"])
"""


@pytest.mark.asyncio
async def test_ob11_call_api_2(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot, group_id=exe_code_group)
        ctx.should_call_api("test_action", {"arg": "ping"}, result=["pong"])
        with ensure_context(bot, event), pytest.raises(KeyError):
            await Context.execute(bot, event, code_test_ob11_call_api_2)


code_test_ob11_call_api_3 = """\
res = await api.test_action(arg="ping")
print(res["key"])
"""


@pytest.mark.asyncio
async def test_ob11_call_api_3(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot, group_id=exe_code_group)
        ctx.should_call_api("test_action", {"arg": "ping"}, result=None)
        with ensure_context(bot, event), pytest.raises(TypeError):
            await Context.execute(bot, event, code_test_ob11_call_api_3)


code_test_ob11_set_card = """\
await api.set_card("test_card")
"""


@pytest.mark.asyncio
async def test_ob11_set_card(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot, group_id=exe_code_group)
        ctx.should_call_api(
            "set_group_card",
            {
                "group_id": event.group_id,
                "user_id": event.user_id,
                "card": "test_card",
            },
        )
        with ensure_context(bot, event):
            await Context.execute(bot, event, code_test_ob11_set_card)

        event, _ = fake_v11_event_session(bot)
        with ensure_context(bot, event), pytest.raises(ValueError, match="未指定群号"):
            await Context.execute(bot, event, code_test_ob11_set_card)


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
async def test_ob11_send_ark(app: App, mocker: MockerFixture) -> None:
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

        event_code, _ = fake_v11_event_session(botV11)
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

        async def _test1() -> None:
            with ensure_context(botV11, event_code):
                await Context.execute(botV11, event_code, code_test_ob11_send_ark)

        async def _test2() -> None:
            await asyncio.sleep(0.01)
            await handle_event(botQQ, event_qq)

        async def _test3() -> None:
            await asyncio.sleep(0.02)
            await handle_event(botV11, event_v11)

        await asyncio.gather(_test1(), _test2(), _test3())


@pytest.mark.asyncio
async def test_ob11_send_ark_fail(app: App, mocker: MockerFixture) -> None:
    import uuid

    from nonebot.adapters.qq import MessageSegment as QQMS
    from nonebot.message import handle_event

    from nonebot_plugin_exe_code.context import Context

    mocker.patch("os.urandom", return_value=b"0" * 16)
    key = f"$ARK-{uuid.uuid4()}$"

    async with app.test_api() as ctx:
        botV11 = fake_v11_bot(ctx, self_id="test-v11")
        botQQ = fake_qq_bot(ctx, self_id="test-qq")

        event_code, _ = fake_v11_event_session(botV11)
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

        async def _test1() -> None:
            with (
                ensure_context(botV11, event_code),
                pytest.raises(RuntimeError, match="test"),
            ):
                await Context.execute(botV11, event_code, code_test_ob11_send_ark)

        async def _test2() -> None:
            await asyncio.sleep(0.01)
            await handle_event(botQQ, event_qq)

        await asyncio.gather(_test1(), _test2())


code_test_ob11_set_mute = """\
await api.set_mute(114514, qid)
"""


@pytest.mark.asyncio
async def test_ob11_set_mute(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot, group_id=exe_code_group)
        ctx.should_call_api(
            "set_group_ban",
            {
                "group_id": event.group_id,
                "user_id": event.user_id,
                "duration": 114514.0,
            },
        )
        with ensure_context(bot, event):
            await Context.execute(bot, event, code_test_ob11_set_mute)

        event, _ = fake_v11_event_session(bot)
        with ensure_context(bot, event), pytest.raises(ValueError, match="未指定群号"):
            await Context.execute(bot, event, code_test_ob11_set_mute)


code_test_ob11_send_like = """\
await api.send_like(10)
"""


@pytest.mark.asyncio
async def test_ob11_send_like(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot, group_id=exe_code_group)
        ctx.should_call_api(
            "send_like",
            {"user_id": event.user_id, "times": 10},
        )
        with ensure_context(bot, event):
            await Context.execute(bot, event, code_test_ob11_send_like)


code_test_ob11_send_private_file = """\
await api.send_private_file("file", "name")
await api.send_private_file("file", "name", "string")
"""


@pytest.mark.asyncio
async def test_ob11_send_private_file(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot)
        ctx.should_call_api(
            "upload_private_file",
            {"user_id": event.user_id, "file": "file", "name": "name"},
        )
        with ensure_context(bot, event), pytest.raises(ValueError, match="不是数字"):
            await Context.execute(bot, event, code_test_ob11_send_private_file)


code_test_ob11_send_group_file = """\
await api.send_group_file("file", "name")
await api.send_group_file("file", "name", "string")
"""


@pytest.mark.asyncio
async def test_ob11_send_group_file(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot, group_id=fake_group_id())
        ctx.should_call_api(
            "upload_group_file",
            {"group_id": event.group_id, "file": "file", "name": "name"},
        )
        with ensure_context(bot, event), pytest.raises(ValueError, match="不是数字"):
            await Context.execute(bot, event, code_test_ob11_send_group_file)

        event, _ = fake_v11_event_session(bot)
        with ensure_context(bot, event), pytest.raises(ValueError, match="未指定群号"):
            await Context.execute(bot, event, code_test_ob11_send_group_file)


code_test_ob11_send_file = """\
await api.send_file("file", "name")
"""


@pytest.mark.asyncio
async def test_ob11_send_file(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot)
        ctx.should_call_api(
            "upload_private_file",
            {"user_id": event.user_id, "file": "file", "name": "name"},
        )
        with ensure_context(bot, event):
            await Context.execute(bot, event, code_test_ob11_send_file)

        event, _ = fake_v11_event_session(bot, group_id=fake_group_id())
        ctx.should_call_api(
            "upload_group_file",
            {"group_id": event.group_id, "file": "file", "name": "name"},
        )
        with ensure_context(bot, event):
            await Context.execute(bot, event, code_test_ob11_send_file)


code_test_ob11_file2str = """\
import io, pathlib

await api.send_file(b"file", "name")
await api.send_file(io.BytesIO(b"file"), "name")
fp = pathlib.Path("__tmp_file__").resolve()
fp.write_bytes(b"file")
await api.send_file(fp, "name")
fp.unlink()
"""


@pytest.mark.asyncio
async def test_ob11_file2str(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot)
        ctx.should_call_api(
            "upload_private_file",
            {"user_id": event.user_id, "file": "base64://ZmlsZQ==", "name": "name"},
        )
        ctx.should_call_api(
            "upload_private_file",
            {"user_id": event.user_id, "file": "base64://ZmlsZQ==", "name": "name"},
        )
        ctx.should_call_api(
            "upload_private_file",
            {"user_id": event.user_id, "file": "base64://ZmlsZQ==", "name": "name"},
        )
        with ensure_context(bot, event):
            await Context.execute(bot, event, code_test_ob11_file2str)


@pytest.mark.asyncio
async def test_ob11_mid(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot)
        ctx.should_call_send(event, Message("1"))
        with ensure_context(bot, event):
            await Context.execute(bot, event, "print(api.mid)")


code_test_ob11_set_reaction = """\
await api.set_reaction(123, api.mid, 456)
"""


@pytest.mark.asyncio
async def test_ob11_set_reaction(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot)

        ctx.should_call_api(
            "set_msg_emoji_like",
            {"message_id": 1, "emoji_id": 123},
            result=None,
        )
        ctx.should_call_api(
            "set_msg_emoji_like",
            {"message_id": 1, "emoji_id": 123},
            exception=ActionFailed(),
        )
        ctx.should_call_api(
            "set_group_reaction",
            {"group_id": 456, "message_id": 1, "code": "123"},
            result=None,
        )
        ctx.should_call_api(
            "set_msg_emoji_like",
            {"message_id": 1, "emoji_id": 123},
            exception=ActionFailed(),
        )
        ctx.should_call_api(
            "set_group_reaction",
            {"group_id": 456, "message_id": 1, "code": "123"},
            exception=ActionFailed(),
        )
        with ensure_context(bot, event):
            await Context.execute(bot, event, code_test_ob11_set_reaction)
            await Context.execute(bot, event, code_test_ob11_set_reaction)
            with pytest.raises(RuntimeError, match="发送消息回应失败"):
                await Context.execute(bot, event, code_test_ob11_set_reaction)


@pytest.mark.asyncio
async def test_ob11_send_fwd(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    expected = Message(
        [
            MessageSegment.node_custom(123, "test", Message("1")),
            MessageSegment.node_custom(0, "forward", Message("2")),
        ]
    )

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)

        event, _ = fake_v11_event_session(bot)
        ctx.should_call_api(
            "send_private_forward_msg",
            {
                "user_id": event.user_id,
                "messages": expected,
            },
            {},
        )
        with ensure_context(bot, event):
            await Context.execute(
                bot,
                event,
                'await api.send_fwd([UserStr("123") @ "1" @ "test", "2"])',
            )

        event, _ = fake_v11_event_session(bot, group_id=fake_group_id())
        ctx.should_call_api(
            "send_group_forward_msg",
            {
                "group_id": event.group_id,
                "messages": expected,
            },
            {},
        )
        with ensure_context(bot, event):
            await Context.execute(
                bot,
                event,
                'await api.send_fwd([UserStr("123") @ "1" @ "test", "2"])',
            )
