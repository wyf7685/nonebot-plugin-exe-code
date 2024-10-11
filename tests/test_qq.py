# ruff: noqa: S101

import pytest
from nonebot.adapters.qq import Message, MessageSegment
from nonebot.adapters.qq.models import (
    MessageArk,
    MessageArkKv,
    MessageArkObj,
    MessageArkObjKv,
)
from nonebug import App

from tests.conftest import exe_code_group
from tests.fake import (
    ensure_context,
    fake_qq_bot,
    fake_qq_event_session,
    fake_qq_guild_exe_code,
    fake_user_id,
)


@pytest.mark.asyncio
async def test_qq(app: App) -> None:
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        bot = fake_qq_bot(ctx)
        user_id = str(fake_user_id())
        event = fake_qq_guild_exe_code(
            user_id,
            str(exe_code_group),
            "test",
            "print(123)",
        )
        ctx.receive_event(bot, event)
        ctx.should_pass_permission()
        ctx.should_call_send(event, Message("123"))
        ctx.should_finished(matcher)


code_test_build_ark = """\
ark = api.build_ark(
    template_id=7685,
    data={
        "#KEY1#": "value",
        "#KEY2#": [
            {"desc": "123"},
            {"desc": "456", "link": "789"},
        ]
    }
)
await api.send_ark(ark)
"""
expected_build_ark = MessageArk(
    template_id=7685,
    kv=[
        MessageArkKv(key="#KEY1#", value="value"),
        MessageArkKv(
            key="#KEY2#",
            obj=[
                MessageArkObj(obj_kv=[MessageArkObjKv(key="desc", value="123")]),
                MessageArkObj(
                    obj_kv=[
                        MessageArkObjKv(key="desc", value="456"),
                        MessageArkObjKv(key="link", value="789"),
                    ]
                ),
            ],
        ),
    ],
)


@pytest.mark.asyncio
async def test_build_send_ark(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_qq_bot(ctx)
        event, session = fake_qq_event_session(bot)
        ctx.should_call_send(event, Message(MessageSegment.ark(expected_build_ark)))
        with ensure_context(bot, event):
            await Context.execute(bot, event, code_test_build_ark)

    assert Context.get_context(session)["ark"] == expected_build_ark


code_test_qq_ark_23 = """\
await api.ark_23("test-desc", "test-prompt", ["line1", ("line2", "url")])
"""
expected_ark_23 = MessageArk(
    template_id=23,
    kv=[
        MessageArkKv(key="#DESC#", value="test-desc"),
        MessageArkKv(key="#PROMPT#", value="test-prompt"),
        MessageArkKv(
            key="#LIST#",
            obj=[
                MessageArkObj(obj_kv=[MessageArkObjKv(key="desc", value="line1")]),
                MessageArkObj(
                    obj_kv=[
                        MessageArkObjKv(key="desc", value="line2"),
                        MessageArkObjKv(key="link", value="url"),
                    ]
                ),
            ],
        ),
    ],
)


@pytest.mark.asyncio
async def test_qq_ark_23(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_qq_bot(ctx)
        event, _ = fake_qq_event_session(bot)
        ctx.should_call_send(event, Message(MessageSegment.ark(expected_ark_23)))
        with ensure_context(bot, event):
            await Context.execute(bot, event, code_test_qq_ark_23)


code_test_qq_ark_24 = """\
await api.ark_24("test-title", "test-desc", "test-prompt", "test-img", "test-url")
"""
expected_ark_24 = MessageArk(
    template_id=24,
    kv=[
        MessageArkKv(key="#TITLE#", value="test-title"),
        MessageArkKv(key="#METADESC#", value="test-desc"),
        MessageArkKv(key="#PROMPT#", value="test-prompt"),
        MessageArkKv(key="#IMG#", value="test-img"),
        MessageArkKv(key="#LINK#", value="test-url"),
    ],
)


@pytest.mark.asyncio
async def test_qq_ark_24(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_qq_bot(ctx)
        event, _ = fake_qq_event_session(bot)
        ctx.should_call_send(event, Message(MessageSegment.ark(expected_ark_24)))
        with ensure_context(bot, event):
            await Context.execute(bot, event, code_test_qq_ark_24)


code_test_qq_ark_37 = """\
await api.ark_37("test-title", "test-subtitle", "test-prompt", "test-img", "test-url")
"""
expected_ark_37 = MessageArk(
    template_id=37,
    kv=[
        MessageArkKv(key="#METATITLE#", value="test-title"),
        MessageArkKv(key="#METASUBTITLE#", value="test-subtitle"),
        MessageArkKv(key="#PROMPT#", value="test-prompt"),
        MessageArkKv(key="#METACOVER#", value="test-img"),
        MessageArkKv(key="#METAURL#", value="test-url"),
    ],
)


@pytest.mark.asyncio
async def test_qq_ark_37(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_qq_bot(ctx)
        event, _ = fake_qq_event_session(bot)
        ctx.should_call_send(event, Message(MessageSegment.ark(expected_ark_37)))
        with ensure_context(bot, event):
            await Context.execute(bot, event, code_test_qq_ark_37)


@pytest.mark.asyncio
async def test_qq_mid(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_qq_bot(ctx)
        event, _ = fake_qq_event_session(bot)
        ctx.should_call_send(event, Message("id"))
        with ensure_context(bot, event):
            await Context.execute(bot, event, "print(api.mid)")
