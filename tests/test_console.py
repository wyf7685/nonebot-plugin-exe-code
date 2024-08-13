import pytest
from nonebot.adapters.console import Adapter, Bot, Message
from nonebug import App

from tests.fake import fake_bot, fake_console_message_event


@pytest.mark.asyncio()
async def test_console(app: App):
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        bot = fake_bot(ctx, Adapter, Bot)
        event = fake_console_message_event(message=Message("code print(123)"))
        ctx.receive_event(bot, event)
        ctx.should_pass_permission(matcher)
        ctx.should_call_send(event, Message("123"))
