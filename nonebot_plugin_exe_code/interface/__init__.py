from nonebot.adapters import Bot, Event

from . import adapters as adapters
from .api import API as API
from .api import api_registry
from .user_const_var import default_context as default_context
from .utils import Buffer as Buffer


def get_api_class(bot: Bot) -> type[API[Bot, Event]]:
    for cls, api in api_registry.items():
        if isinstance(bot.adapter, cls):
            return api
    return API
