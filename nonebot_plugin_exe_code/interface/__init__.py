from nonebot.adapters import Bot, Event
from nonebot_plugin_user.models import UserSession

from ..typings import T_Context
from . import adapters as adapters
from .api import API as API
from .api import api_registry
from .user_const_var import get_default_context as get_default_context
from .utils import Buffer as Buffer


async def create_api(
    bot: Bot,
    event: Event,
    context: T_Context,
    session: UserSession,
) -> API[Bot, Event]:
    for cls in api_registry:
        if isinstance(bot.adapter, cls):
            api = api_registry[cls]
            break
    else:
        api = API

    assert session is not None, "Session is None"
    return api(bot, event, session, context)
