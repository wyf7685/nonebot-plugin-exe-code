# ruff: noqa: N806, N814


import pytest
from nonebot.adapters.onebot.v11 import ActionFailed, Message, MessageSegment
from nonebot.adapters.onebot.v11.event import Reply, Sender
from nonebug import App

from .conftest import exe_code_group
from .fake.common import ensure_context, fake_group_id
from .fake.onebot11 import fake_v11_bot, fake_v11_event_session

code_test_ob11_img_summary = """\
await api.img_summary("test")
"""


@pytest.mark.asyncio
async def test_ob11_img_summary(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.exception import ParamMissing

    url = "http://localhost:8080/image.png"
    expected = Message(MessageSegment.image(url))
    expected[0].data["summary"] = "test"

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, session = fake_v11_event_session(bot, group_id=exe_code_group)
        with ensure_context(bot, event), pytest.raises(ParamMissing, match="无效 url"):
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
    from nonebot_plugin_exe_code.exception import ParamMissing

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
        with (
            ensure_context(bot, event),
            pytest.raises(ParamMissing, match="未指定群号"),
        ):
            await Context.execute(bot, event, code_test_ob11_set_card)


code_test_ob11_set_mute = """\
await api.set_mute(114514, uid)
"""


@pytest.mark.asyncio
async def test_ob11_set_mute(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.exception import ParamMissing

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
        with (
            ensure_context(bot, event),
            pytest.raises(ParamMissing, match="未指定群号"),
        ):
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
    from nonebot_plugin_exe_code.exception import ParamMismatch

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot)
        ctx.should_call_api(
            "upload_private_file",
            {"user_id": event.user_id, "file": "file", "name": "name"},
        )
        with ensure_context(bot, event), pytest.raises(ParamMismatch, match="不是数字"):
            await Context.execute(bot, event, code_test_ob11_send_private_file)


code_test_ob11_send_group_file = """\
await api.send_group_file("file", "name")
await api.send_group_file("file", "name", "string")
"""


@pytest.mark.asyncio
async def test_ob11_send_group_file(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.exception import ParamMismatch, ParamMissing

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot, group_id=fake_group_id())
        ctx.should_call_api(
            "upload_group_file",
            {"group_id": event.group_id, "file": "file", "name": "name"},
        )
        with ensure_context(bot, event), pytest.raises(ParamMismatch, match="不是数字"):
            await Context.execute(bot, event, code_test_ob11_send_group_file)

        event, _ = fake_v11_event_session(bot)
        with (
            ensure_context(bot, event),
            pytest.raises(ParamMissing, match="未指定群号"),
        ):
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


code_test_ob11_get_platform = """\
print(await api.get_platform())
"""


@pytest.mark.asyncio
async def test_ob11_get_platform(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    expected = Message(MessageSegment.text("[OneBot V11] app_name app_version"))

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot)
        ctx.should_call_api(
            "get_version_info",
            {},
            {"app_name": "app_name", "app_version": "app_version"},
        )
        ctx.should_call_send(event, expected)
        with ensure_context(bot, event):
            await Context.execute(bot, event, code_test_ob11_get_platform)


@pytest.mark.asyncio
async def test_ob11_set_reaction(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.exception import APICallFailed

    code_test_ob11_set_reaction_1 = "await api.set_reaction(123, api.mid, 456)"
    code_test_ob11_set_reaction_2 = "await api.set_reaction(123, api.mid)"
    code_test_ob11_set_reaction_3 = "await api.set_reaction(123)"

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot)

        # 1. NapCat
        ctx.should_call_api(
            "get_version_info",
            {},
            {"app_name": "NapCat", "app_version": "app_version"},
        )
        ctx.should_call_api(
            "set_msg_emoji_like",
            {"message_id": 1, "emoji_id": 123},
            result=None,
        )
        with ensure_context(bot, event):
            await Context.execute(bot, event, code_test_ob11_set_reaction_1)

        # 2. LLOneBot
        ctx.should_call_api(
            "get_version_info",
            {},
            {"app_name": "LLOneBot", "app_version": "app_version"},
        )
        ctx.should_call_api(
            "set_msg_emoji_like",
            {"message_id": 1, "emoji_id": 123},
            result=None,
        )
        with ensure_context(bot, event):
            await Context.execute(bot, event, code_test_ob11_set_reaction_1)

        # 3. Lagrange with gid
        ctx.should_call_api(
            "get_version_info",
            {},
            {"app_name": "Lagrange", "app_version": "app_version"},
        )
        ctx.should_call_api(
            "set_group_reaction",
            {"group_id": 456, "message_id": 1, "code": "123"},
            result=None,
        )
        with ensure_context(bot, event):
            await Context.execute(bot, event, code_test_ob11_set_reaction_1)

        # 3. Lagrange without gid
        ctx.should_call_api(
            "get_version_info",
            {},
            {"app_name": "Lagrange", "app_version": "app_version"},
        )
        with ensure_context(bot, event), pytest.raises(TypeError, match="Lagrange"):
            await Context.execute(bot, event, code_test_ob11_set_reaction_2)

        # 4. Unkown platform
        ctx.should_call_api(
            "get_version_info",
            {},
            {"app_name": "Unkown Platform", "app_version": "app_version"},
        )
        with (
            ensure_context(bot, event),
            pytest.raises(APICallFailed, match="unkown platform"),
        ):
            await Context.execute(bot, event, code_test_ob11_set_reaction_1)

        # 5. without mid
        event.reply = Reply(
            time=1000000,
            message_type="test",
            message_id=111,
            real_id=1,
            sender=Sender(
                card="",
                nickname="test",
                role="member",
            ),
            message=Message(),
        )
        ctx.should_call_api(
            "get_version_info",
            {},
            {"app_name": "NapCat", "app_version": "app_version"},
        )
        ctx.should_call_api(
            "set_msg_emoji_like",
            {"message_id": 111, "emoji_id": 123},
            result=None,
        )
        with ensure_context(bot, event):
            await Context.execute(bot, event, code_test_ob11_set_reaction_3)


@pytest.mark.asyncio
async def test_ob11_group_poke(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.exception import ParamMissing

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)

        event, _ = fake_v11_event_session(bot, group_id=fake_group_id())
        ctx.should_call_api(
            "group_poke",
            {"group_id": event.group_id, "user_id": event.user_id},
        )
        with ensure_context(bot, event):
            await Context.execute(bot, event, "await api.group_poke(uid)")

        event, _ = fake_v11_event_session(bot)
        with (
            ensure_context(bot, event),
            pytest.raises(ParamMissing, match="未指定群号"),
        ):
            await Context.execute(bot, event, "await api.group_poke(uid)")

        event, _ = fake_v11_event_session(bot, group_id=fake_group_id())
        ctx.should_call_api(
            "group_poke",
            {"group_id": event.group_id, "user_id": event.user_id},
        )
        with ensure_context(bot, event):
            await Context.execute(bot, event, "await api.group_poke(uid, gid)")
