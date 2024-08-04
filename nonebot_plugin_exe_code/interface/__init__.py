from nonebot.adapters import Bot

from . import adapter_api as adapter_api
from .api import API as API
from .api import api_registry
from .user_const_var import default_context as default_context
from .utils import Buffer as Buffer


def get_api_class(bot: Bot) -> type[API]:
    for cls, api in api_registry.items():
        if isinstance(bot.adapter, cls):
            return api
    return API
