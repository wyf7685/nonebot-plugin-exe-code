from nonebot.adapters import Adapter, Bot

from . import adapter_api as _
from .api import API as API
from .api import api_registry
from .user_const_var import default_context as default_context
from .utils import Buffer as Buffer


def get_api_class(bot: Bot):
    adapters = set(api_registry.keys())
    adapters.remove(Adapter)

    for cls in adapters:
        if isinstance(bot.adapter, cls):
            return api_registry[cls]
    return API
