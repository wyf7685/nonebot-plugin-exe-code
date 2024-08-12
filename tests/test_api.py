import pytest
from nonebot.adapters.onebot.v11 import Adapter, Bot, Message, MessageSegment
from nonebug import App
import dataclasses

from tests.conftest import superuser
from tests.fake import ensure_context, fake_event_session, fake_group_id, fake_user_id


@pytest.mark.asyncio()
async def test_help(app: App):
    from nonebot_plugin_exe_code.constant import INTERFACE_METHOD_DESCRIPTION
    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.interface.api import API
    from nonebot_plugin_exe_code.interface.help_doc import FuncDescription

    async with app.test_api() as ctx:
        adapter = ctx.create_adapter(base=Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        bot.adapter.__class__.get_name = Adapter.get_name

        event, session = fake_event_session(bot)
        help_desc: FuncDescription = getattr(
            API.set_const, INTERFACE_METHOD_DESCRIPTION
        )
        expected = Message(f"api.{help_desc.format(API.set_const)}")
        ctx.should_call_send(event, expected)
        with ensure_context(bot, event):
            await Context.execute(bot, session, "await help(api.set_const)")


@pytest.mark.asyncio()
async def test_superuser(app: App):
    from nonebot_plugin_exe_code.config import config
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        adapter = ctx.create_adapter(base=Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        bot.adapter.__class__.get_name = Adapter.get_name

        event, session = fake_event_session(bot, superuser)
        user_id, group_id = fake_user_id(), fake_group_id()

        ctx.should_call_send(event, Message("123"))
        with ensure_context(bot, event):
            await Context.execute(
                bot,
                session,
                f"set_usr({user_id})\n"
                f"set_grp({group_id})\n"
                "get_ctx(qid)['var'] = 123\n"
                "print(var)",
            )

        assert str(user_id) in config.user
        assert str(group_id) in config.group


@pytest.mark.asyncio()
async def test_send_limit(app: App):
    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.interface.utils import ReachLimit

    async with app.test_api() as ctx:
        adapter = ctx.create_adapter(base=Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        bot.adapter.__class__.get_name = Adapter.get_name

        event, session = fake_event_session(bot)

        for i in range(6):
            ctx.should_call_send(event, Message(str(i)))

        with ensure_context(bot, event):
            with pytest.raises(ReachLimit):
                await Context.execute(
                    bot,
                    session,
                    "for i in range(7): await feedback(i)",
                )


@pytest.mark.asyncio()
async def test_is_group(app: App):
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        adapter = ctx.create_adapter(base=Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)
        bot.adapter.__class__.get_name = Adapter.get_name

        code = "print(api.is_group())"

        event, session = fake_event_session(bot)
        ctx.should_call_send(event, Message("False"))
        with ensure_context(bot, event):
            await Context.execute(bot, session, code)

        event, session = fake_event_session(bot, group_id=fake_group_id())
        ctx.should_call_send(event, Message("True"))
        with ensure_context(bot, event):
            await Context.execute(bot, session, code)


# XXX: alc uniseg 在处理 ob11 合并转发时有 bug, 等修复后继续写测试

# @pytest.mark.asyncio()
# async def test_send_private_forward(app: App):
#     from nonebot_plugin_exe_code.context import Context

#     async with app.test_api() as ctx:
#         adapter = ctx.create_adapter(base=Adapter)
#         bot = ctx.create_bot(base=Bot, adapter=adapter)
#         bot.adapter.__class__.get_name = Adapter.get_name

#         event, session = fake_event_session(bot)
#         expected = [
#             MessageSegment.node_custom(0, "forward", Message("1")),
#             MessageSegment.node_custom(0, "forward", Message("2")),
#         ]
#         ctx.should_call_api(
#             "send_private_forward_msg",
#             {
#                 "user_id": event.user_id,
#                 "messages": expected,
#             },
#             {},
#         )
#         with ensure_context(bot, event):
#             await Context.execute(
#                 bot,
#                 session,
#                 'await feedback(["1", "2"], fwd=True)',
#             )
