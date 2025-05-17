# ruff: noqa: N806, N814


import pytest
from nonebot.adapters.onebot.v11 import ActionFailed, Message, MessageSegment
from nonebot.adapters.onebot.v11.event import Reply, Sender
from nonebug import App

from .conftest import exe_code_group
from .fake.common import fake_group_id
from .fake.onebot11 import ensure_v11_api


@pytest.mark.asyncio
async def test_ob11_img_summary(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.exception import ParamMissing

    url = "http://localhost:8080/image.png"
    expected = Message(MessageSegment.image(url))
    expected[0].data["summary"] = "test"

    async with (
        app.test_api() as ctx,
        ensure_v11_api(ctx, group_id=exe_code_group) as api,
    ):
        with pytest.raises(ParamMissing, match="无效 url"):
            await api.img_summary("test")

        Context.get_context(api.session).ctx["gurl"] = url
        ctx.should_call_send(api.event, expected)
        await api.img_summary("test")


@pytest.mark.asyncio
async def test_ob11_recall(app: App) -> None:
    async with (
        app.test_api() as ctx,
        ensure_v11_api(ctx, group_id=exe_code_group) as api,
    ):
        ctx.should_call_api("delete_msg", {"message_id": 1}, {})
        await api.recall(1)


@pytest.mark.asyncio
async def test_ob11_get_msg(app: App) -> None:
    async with (
        app.test_api() as ctx,
        ensure_v11_api(ctx, group_id=exe_code_group) as api,
    ):
        ctx.should_call_api(
            "get_msg",
            {"message_id": 1},
            {"raw_message": "123"},
        )
        assert await api.get_msg(1) == Message("123")


@pytest.mark.asyncio
async def test_ob11_get_fwd(app: App) -> None:
    async with (
        app.test_api() as ctx,
        ensure_v11_api(ctx, group_id=exe_code_group) as api,
    ):
        ctx.should_call_api(
            "get_forward_msg",
            {"message_id": 1},
            {"messages": [{"raw_message": "123"}]},
        )
        assert (await api.get_fwd(1))[0] == Message("123")


@pytest.mark.asyncio
async def test_ob11_exception(app: App) -> None:
    async with (
        app.test_api() as ctx,
        ensure_v11_api(ctx, group_id=exe_code_group) as api,
    ):
        ctx.should_call_api("not_an_action", {"arg": 123}, exception=ActionFailed())
        res = await api.not_an_action(arg=123)
        assert isinstance(res.error, ActionFailed)

        ctx.should_call_api("not_an_action", {"arg": 123}, exception=Exception())
        with pytest.raises(Exception, match="TEST"):
            await api.not_an_action(arg=123, raise_text="TEST")

        with pytest.raises(AttributeError):
            _ = api.__not_an_attr__


@pytest.mark.asyncio
async def test_ob11_call_api(app: App) -> None:
    async with (
        app.test_api() as ctx,
        ensure_v11_api(ctx, group_id=exe_code_group) as api,
    ):
        ctx.should_call_api("test_action", {"arg": "ping"}, result=["pong"])
        res = await api.test_action(arg="ping")
        assert res[0] == "pong"

        ctx.should_call_api("test_action", {"arg": "ping"}, result={"key": "pong"})
        res = await api.test_action(arg="ping")
        assert res["key"] == "pong"

        ctx.should_call_api("test_action", {"arg": "ping"}, result=None)
        res = await api.test_action(arg="ping")
        with pytest.raises(TypeError):
            _ = res["key"]


@pytest.mark.asyncio
async def test_ob11_set_card(app: App) -> None:
    async with (
        app.test_api() as ctx,
        ensure_v11_api(ctx, group_id=exe_code_group) as api,
    ):
        ctx.should_call_api(
            "set_group_card",
            {
                "group_id": exe_code_group,
                "user_id": api.event.user_id,
                "card": "test_card",
            },
        )
        await api.set_card("test_card")


@pytest.mark.asyncio
async def test_ob11_set_card_failed(app: App) -> None:
    from nonebot_plugin_exe_code.exception import ParamMissing

    async with app.test_api() as ctx, ensure_v11_api(ctx) as api:
        with pytest.raises(ParamMissing, match="未指定群号"):
            await api.set_card("test_card")


@pytest.mark.asyncio
async def test_ob11_set_mute(app: App) -> None:
    async with (
        app.test_api() as ctx,
        ensure_v11_api(ctx, group_id=exe_code_group) as api,
    ):
        ctx.should_call_api(
            "set_group_ban",
            {
                "group_id": exe_code_group,
                "user_id": api.event.user_id,
                "duration": 114514.0,
            },
        )
        await api.set_mute(114514, uid=api.uid)


@pytest.mark.asyncio
async def test_ob11_set_mute_failed(app: App) -> None:
    from nonebot_plugin_exe_code.exception import ParamMissing

    async with app.test_api() as ctx, ensure_v11_api(ctx) as api:
        with pytest.raises(ParamMissing, match="未指定群号"):
            await api.set_mute(114514, uid=api.uid)


code_test_ob11_send_like = """\
await api.send_like(10)
"""


@pytest.mark.asyncio
async def test_ob11_send_like(app: App) -> None:
    async with (
        app.test_api() as ctx,
        ensure_v11_api(ctx, group_id=exe_code_group) as api,
    ):
        ctx.should_call_api(
            "send_like",
            {"user_id": api.event.user_id, "times": 10},
        )
        await api.send_like(10)


@pytest.mark.asyncio
async def test_ob11_send_private_file(app: App) -> None:
    from nonebot_plugin_exe_code.exception import ParamMismatch

    async with (
        app.test_api() as ctx,
        ensure_v11_api(ctx, group_id=exe_code_group) as api,
    ):
        ctx.should_call_api(
            "upload_private_file",
            {"user_id": api.event.user_id, "file": "file", "name": "name"},
        )
        await api.send_private_file("file", "name")

        with pytest.raises(ParamMismatch, match="不是数字"):
            await api.send_private_file("file", "name", "string")


@pytest.mark.asyncio
async def test_ob11_send_group_file(app: App) -> None:
    from nonebot_plugin_exe_code.exception import ParamMismatch, ParamMissing

    async with (
        app.test_api() as ctx,
        ensure_v11_api(ctx, group_id=exe_code_group) as api,
    ):
        ctx.should_call_api(
            "upload_group_file",
            {"group_id": exe_code_group, "file": "file", "name": "name"},
        )
        await api.send_group_file("file", "name")

        with pytest.raises(ParamMismatch, match="不是数字"):
            await api.send_group_file("file", "name", "string")

    async with app.test_api() as ctx, ensure_v11_api(ctx) as api:
        with pytest.raises(ParamMissing, match="未指定群号"):
            await api.send_group_file("file", "name")


@pytest.mark.asyncio
async def test_ob11_send_file(app: App) -> None:
    async with app.test_api() as ctx, ensure_v11_api(ctx) as api:
        ctx.should_call_api(
            "upload_private_file",
            {"user_id": api.event.user_id, "file": "file", "name": "name"},
        )
        await api.send_file("file", "name")

    group_id = fake_group_id()
    async with app.test_api() as ctx, ensure_v11_api(ctx, group_id=group_id) as api:
        ctx.should_call_api(
            "upload_group_file",
            {"group_id": group_id, "file": "file", "name": "name"},
        )
        await api.send_file("file", "name")


@pytest.mark.asyncio
async def test_ob11_file2str(app: App) -> None:
    import io
    import pathlib

    async with app.test_api() as ctx, ensure_v11_api(ctx) as api:
        user_id = api.event.user_id

        ctx.should_call_api(
            "upload_private_file",
            {"user_id": user_id, "file": "base64://ZmlsZQ==", "name": "name"},
        )
        await api.send_file(b"file", "name")

        ctx.should_call_api(
            "upload_private_file",
            {"user_id": user_id, "file": "base64://ZmlsZQ==", "name": "name"},
        )
        await api.send_file(io.BytesIO(b"file"), "name")

        ctx.should_call_api(
            "upload_private_file",
            {"user_id": user_id, "file": "base64://ZmlsZQ==", "name": "name"},
        )
        fp = pathlib.Path("__tmp_file__").resolve()
        fp.write_bytes(b"file")
        await api.send_file(fp, "name")
        fp.unlink()


@pytest.mark.asyncio
async def test_ob11_mid(app: App) -> None:
    async with app.test_api() as ctx, ensure_v11_api(ctx) as api:
        assert api.mid == "1"


@pytest.mark.asyncio
async def test_ob11_send_fwd(app: App) -> None:
    from nonebot_plugin_exe_code.typings import UserStr

    expected = Message(
        [
            MessageSegment.node_custom(123, "test", Message("1")),
            MessageSegment.node_custom(0, "forward", Message("2")),
        ]
    )

    async with app.test_api() as ctx, ensure_v11_api(ctx) as api:
        ctx.should_call_api(
            "send_private_forward_msg",
            {
                "user_id": api.event.user_id,
                "messages": expected,
            },
            {},
        )
        await api.send_fwd([UserStr("123") @ "1" @ "test", "2"])

    group_id = fake_group_id()
    async with app.test_api() as ctx, ensure_v11_api(ctx, group_id=group_id) as api:
        ctx.should_call_api(
            "send_group_forward_msg",
            {"group_id": group_id, "messages": expected},
            {},
        )
        await api.send_fwd([UserStr("123") @ "1" @ "test", "2"])


@pytest.mark.asyncio
async def test_ob11_get_platform(app: App) -> None:
    async with app.test_api() as ctx, ensure_v11_api(ctx) as api:
        ctx.should_call_api(
            "get_version_info",
            {},
            {"app_name": "app_name", "app_version": "app_version"},
        )
        assert await api.get_platform() == "[OneBot V11] app_name app_version"


@pytest.mark.asyncio
async def test_ob11_set_reaction(app: App) -> None:
    from nonebot_plugin_exe_code.exception import APICallFailed

    async with app.test_api() as ctx, ensure_v11_api(ctx) as api:
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
        await api.set_reaction(123, api.mid, 456)

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
        await api.set_reaction(123, api.mid, 456)

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
        await api.set_reaction(123, api.mid, 456)

        # 3. Lagrange without gid
        ctx.should_call_api(
            "get_version_info",
            {},
            {"app_name": "Lagrange", "app_version": "app_version"},
        )
        with pytest.raises(TypeError, match="Lagrange"):
            await api.set_reaction(123, api.mid)

        # 4. Unkown platform
        ctx.should_call_api(
            "get_version_info",
            {},
            {"app_name": "Unkown Platform", "app_version": "app_version"},
        )
        with pytest.raises(APICallFailed, match="unkown platform"):
            await api.set_reaction(123, api.mid, 456)

        # 5. without mid
        api.event.reply = Reply(
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
        await api.set_reaction(123)


@pytest.mark.asyncio
async def test_ob11_group_poke(app: App) -> None:
    from nonebot_plugin_exe_code.exception import ParamMissing

    group_id = fake_group_id()
    async with app.test_api() as ctx, ensure_v11_api(ctx, group_id=group_id) as api:
        ctx.should_call_api(
            "group_poke",
            {"group_id": group_id, "user_id": api.event.user_id},
        )
        await api.group_poke(api.uid)

        ctx.should_call_api(
            "group_poke",
            {"group_id": group_id, "user_id": api.event.user_id},
        )
        await api.group_poke(api.uid, api.gid)

    async with app.test_api() as ctx, ensure_v11_api(ctx) as api:
        with pytest.raises(ParamMissing, match="未指定群号"):
            await api.group_poke(api.uid)
