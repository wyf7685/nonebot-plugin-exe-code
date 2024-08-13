import pytest
from nonebot.adapters.qq import Adapter, Bot, Message
from nonebot.adapters.qq.config import BotInfo
from nonebug import App

from tests.conftest import exe_code_group
from tests.fake import fake_bot, fake_qq_guild_exe_code, fake_user_id


@pytest.mark.asyncio()
async def test_qq(app: App):
    from nonebot_plugin_exe_code.matchers.code import matcher

    async with app.test_matcher(matcher) as ctx:
        bot = fake_bot(
            ctx,
            Adapter,
            Bot,
            bot_info=BotInfo(
                id="app_id",
                token="app_token",
                secret="app_secret",
            ),
        )

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
