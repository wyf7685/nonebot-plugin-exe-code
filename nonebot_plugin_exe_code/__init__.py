from nonebot import require
from nonebot.plugin import PluginMetadata
from nonebot.plugin.load import inherit_supported_adapters

requirements = {
    "nonebot_plugin_alconna",
    "nonebot_plugin_datastore",
    "nonebot_plugin_session",
    "nonebot_plugin_userinfo",
}
[require(i) for i in requirements]

from . import matchers as _
from .config import Config

__version__ = "1.0.3"
__plugin_meta__ = PluginMetadata(
    name="exe_code",
    description="在对话中执行 Python 代码",
    usage="code {Your code here...}",
    type="application",
    homepage="https://github.com/wyf7685/nonebot-plugin-exe-code",
    config=Config,
    supported_adapters=inherit_supported_adapters(*requirements),
    extra={
        "author": "wyf7685",
        "version": __version__,
    },
)
