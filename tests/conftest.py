import os

import nonebot
import pytest

from nonebot.adapters.console import Adapter as ConsoleAdapter
from nonebot.adapters.qq import Adapter as QQAdapter
from nonebot.adapters.onebot.v11 import Adapter as Onebot11Adapter
from nonebug import NONEBOT_INIT_KWARGS, App

superuser = 7685
exe_code_user = 114514
exe_code_group = 1919810


def pytest_configure(config: pytest.Config):
    config.stash[NONEBOT_INIT_KWARGS] = {
        "driver": "~fastapi+~httpx+~websockets",
        "log_level": "TRACE",
        "host": "0.0.0.0",
        "port": "8090",
        "superusers": [str(superuser)],
        "exe_code": {
            "user": [str(exe_code_user)],
            "group": [str(exe_code_group)],
            "qbot_id": 0,
        },
    }
    os.environ["PLUGIN_ALCONNA_TESTENV"] = "1"


@pytest.fixture()
async def app():
    # 加载插件
    nonebot.require("nonebot_plugin_exe_code")

    from nonebot_plugin_exe_code.interface.user_const_var import DATA_DIR

    exist = [i.name for i in DATA_DIR.iterdir()]

    yield App()

    for fp in DATA_DIR.iterdir():
        if fp.name not in exist:
            fp.unlink()


@pytest.fixture(scope="session", autouse=True)
def load_bot():
    # 加载适配器
    driver = nonebot.get_driver()
    driver.register_adapter(ConsoleAdapter)
    driver.register_adapter(QQAdapter)
    driver.register_adapter(Onebot11Adapter)

    return None
