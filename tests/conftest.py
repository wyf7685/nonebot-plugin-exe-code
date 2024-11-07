import os
from collections.abc import AsyncGenerator

import nonebot
import pytest
from nonebot.adapters import console, onebot, qq, satori, telegram
from nonebug import NONEBOT_INIT_KWARGS, App

superuser = 7685000
exe_code_user = 114514
exe_code_group = 1919810
exe_code_qbot_id = 10007685


def pytest_configure(config: pytest.Config) -> None:
    config.stash[NONEBOT_INIT_KWARGS] = {
        "driver": "~fastapi+~httpx+~websockets",
        "log_level": "TRACE",
        "host": "127.0.0.1",
        "port": "8080",
        "superusers": [str(superuser)],
        "exe_code": {
            "user": [str(exe_code_user)],
            "group": [str(exe_code_group)],
            "qbot_id": exe_code_qbot_id,
        },
    }
    os.environ["PLUGIN_ALCONNA_TESTENV"] = "1"


@pytest.fixture
async def app() -> AsyncGenerator[App, None]:
    # 加载插件
    nonebot.require("nonebot_plugin_exe_code")

    from nonebot_plugin_exe_code.constant import DATA_DIR

    exist_file = {i.name for i in DATA_DIR.iterdir()}

    yield App()

    for fp in DATA_DIR.iterdir():
        if fp.name not in exist_file:
            fp.unlink()


@pytest.fixture(scope="session", autouse=True)
def _load_bot() -> None:
    # 加载适配器
    driver = nonebot.get_driver()
    driver.register_adapter(console.Adapter)
    driver.register_adapter(onebot.v11.Adapter)
    driver.register_adapter(qq.Adapter)
    driver.register_adapter(satori.Adapter)
    driver.register_adapter(telegram.Adapter)


@pytest.fixture(autouse=True)
async def _gtg() -> None:
    nonebot.require("nonebot_plugin_exe_code")
    from nonebot_plugin_exe_code.interface.utils import GlobalTaskGroup

    await GlobalTaskGroup.on_startup()
