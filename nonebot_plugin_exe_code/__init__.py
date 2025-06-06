from importlib.metadata import version

from nonebot import require
from nonebot.plugin import PluginMetadata
from nonebot.plugin.load import inherit_supported_adapters

require("nonebot_plugin_alconna")
require("nonebot_plugin_localstore")
require("nonebot_plugin_user")
require("nonebot_plugin_waiter")

from . import matchers as matchers
from .config import Config

try:
    __version__ = version("nonebot-plugin-exe-code")
except Exception:
    __version__ = None

__plugin_meta__ = PluginMetadata(
    name="nonebot-plugin-exe-code",
    description="在对话中执行 Python 代码",
    usage='code print("Hello world!")',
    type="application",
    homepage="https://github.com/wyf7685/nonebot-plugin-exe-code",
    config=Config,
    supported_adapters=inherit_supported_adapters(
        "nonebot_plugin_alconna",
        "nonebot_plugin_user",
        "nonebot_plugin_waiter",
    ),
    extra={
        "author": "wyf7685",
        "version": __version__,
    },
)
