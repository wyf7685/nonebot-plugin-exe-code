import pytest
from nonebot.adapters.onebot.v11 import ActionFailed, Message, MessageSegment
from nonebug import App

from tests.conftest import exe_code_group
from tests.fake import ensure_context, fake_v11_bot, fake_v11_event_session

code_test_ob11_img_summary = """\
await api.img_summary("test")
"""


@pytest.mark.asyncio()
async def test_ob11_img_summary(app: App):
    from nonebot_plugin_exe_code.context import Context

    url = "http://localhost:8080/image.png"
    expected = Message(MessageSegment.image(url))
    expected[0].data["summary"] = "test"

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, session = fake_v11_event_session(bot, group_id=exe_code_group)
        with ensure_context(bot, event), pytest.raises(ValueError, match="无效 url"):
            await Context.execute(bot, session, code_test_ob11_img_summary)
        Context.get_context(session).set_value("gurl", url)
        ctx.should_call_send(event, expected)
        with ensure_context(bot, event):
            await Context.execute(bot, session, code_test_ob11_img_summary)


code_test_ob11_recall = """\
await recall(1)
"""


@pytest.mark.asyncio()
async def test_ob11_recall(app: App):
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, session = fake_v11_event_session(bot, group_id=exe_code_group)
        ctx.should_call_api("delete_msg", {"message_id": 1}, {})
        with ensure_context(bot, event):
            await Context.execute(bot, session, code_test_ob11_recall)


code_test_ob11_get_msg = """\
print(await get_msg(1))
"""


@pytest.mark.asyncio()
async def test_ob11_get_msg(app: App):
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, session = fake_v11_event_session(bot, group_id=exe_code_group)
        ctx.should_call_api(
            "get_msg",
            {"message_id": 1},
            {"raw_message": "123"},
        )
        ctx.should_call_send(event, Message("123"))
        with ensure_context(bot, event):
            await Context.execute(bot, session, code_test_ob11_get_msg)


code_test_ob11_get_fwd = """\
print((await get_fwd(1))[0])
"""


@pytest.mark.asyncio()
async def test_ob11_get_fwd(app: App):
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, session = fake_v11_event_session(bot, group_id=exe_code_group)
        ctx.should_call_api(
            "get_forward_msg",
            {"message_id": 1},
            {"messages": [{"raw_message": "123"}]},
        )
        ctx.should_call_send(event, Message("123"))
        with ensure_context(bot, event):
            await Context.execute(bot, session, code_test_ob11_get_fwd)


code_test_ob11_exception_1 = """\
res = await api.not_an_action(arg=123)
raise res.error
"""


@pytest.mark.asyncio()
async def test_ob11_exception_1(app: App):
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, session = fake_v11_event_session(bot, group_id=exe_code_group)
        ctx.should_call_api("not_an_action", {"arg": 123}, exception=ActionFailed())
        with ensure_context(bot, event), pytest.raises(ActionFailed):
            await Context.execute(bot, session, code_test_ob11_exception_1)


code_test_ob11_exception_2 = """\
print(await api.not_an_action(arg=123))
"""


@pytest.mark.asyncio()
async def test_ob11_exception_2(app: App):
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, session = fake_v11_event_session(bot, group_id=exe_code_group)
        ctx.should_call_api("not_an_action", {"arg": 123}, exception=Exception())
        ctx.should_call_send(event, Message("<Result error=Exception()>"))
        with ensure_context(bot, event):
            await Context.execute(bot, session, code_test_ob11_exception_2)


code_test_ob11_exception_3 = """\
try:
    await api.not_an_action(arg=123, raise_text="TEST")
except Exception as err:
    print(repr(err))
"""


@pytest.mark.asyncio()
async def test_ob11_exception_3(app: App):
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, session = fake_v11_event_session(bot, group_id=exe_code_group)
        ctx.should_call_api("not_an_action", {"arg": 123}, exception=Exception())
        ctx.should_call_send(event, Message("RuntimeError('TEST')"))
        with ensure_context(bot, event):
            await Context.execute(bot, session, code_test_ob11_exception_3)


code_test_ob11_exception_4 = """\
print(api.__not_an_attr__)
"""


@pytest.mark.asyncio()
async def test_ob11_exception_4(app: App):
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, session = fake_v11_event_session(bot, group_id=exe_code_group)
        with ensure_context(bot, event), pytest.raises(AttributeError):
            await Context.execute(bot, session, code_test_ob11_exception_4)


code_test_ob11_call_api_1 = """\
res = await api.test_action(arg="ping")
print(res)
print(res[0])
"""


@pytest.mark.asyncio()
async def test_ob11_call_api_1(app: App):
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, session = fake_v11_event_session(bot, group_id=exe_code_group)
        ctx.should_call_api("test_action", {"arg": "ping"}, result=["pong"])
        ctx.should_call_send(
            event,
            Message(MessageSegment.text("<Result data=['pong']>\npong")),
        )
        with ensure_context(bot, event):
            await Context.execute(bot, session, code_test_ob11_call_api_1)


code_test_ob11_call_api_2 = """\
res = await api.test_action(arg="ping")
print(res["key"])
"""


@pytest.mark.asyncio()
async def test_ob11_call_api_2(app: App):
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, session = fake_v11_event_session(bot, group_id=exe_code_group)
        ctx.should_call_api("test_action", {"arg": "ping"}, result=["pong"])
        with ensure_context(bot, event), pytest.raises(KeyError):
            await Context.execute(bot, session, code_test_ob11_call_api_2)


code_test_ob11_call_api_3 = """\
res = await api.test_action(arg="ping")
print(res["key"])
"""


@pytest.mark.asyncio()
async def test_ob11_call_api_3(app: App):
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, session = fake_v11_event_session(bot, group_id=exe_code_group)
        ctx.should_call_api("test_action", {"arg": "ping"}, result=None)
        with ensure_context(bot, event), pytest.raises(TypeError):
            await Context.execute(bot, session, code_test_ob11_call_api_3)
