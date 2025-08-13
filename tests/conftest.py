import os
import shutil
import tempfile
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

import nonebot
import pytest
from nonebot.adapters import console, onebot, qq, satori, telegram
from nonebug import NONEBOT_INIT_KWARGS, App

superuser = 7685000
exe_code_user = 114514
exe_code_group = 1919810


def pytest_configure(config: pytest.Config) -> None:
    config.stash[NONEBOT_INIT_KWARGS] = {
        "driver": "~fastapi+~httpx+~websockets",
        "log_level": "TRACE",
        "host": "127.0.0.1",
        "port": "8080",
        "superusers": [str(superuser)],
        "sqlalchemy_database_url": "sqlite+aiosqlite://",
        "alembic_startup_check": False,
        "exe_code": {
            "user": [str(exe_code_user)],
            "group": [str(exe_code_group)],
        },
    }
    os.environ["PLUGIN_ALCONNA_TESTENV"] = "1"


@pytest.fixture(scope="session", params=[pytest.param("asyncio"), pytest.param("trio")])
def anyio_backend(request: pytest.FixtureRequest) -> Any:
    return request.param


@pytest.fixture(scope="session", autouse=True)
async def _fix_localstore() -> AsyncGenerator[None]:
    localstore_root = Path(tempfile.mkdtemp())

    driver = nonebot.get_driver()
    for key in "cache", "config", "data":
        setattr(driver.config, f"localstore_{key}_dir", str(localstore_root / key))

    try:
        yield
    finally:
        shutil.rmtree(localstore_root, ignore_errors=True)


@pytest.fixture
async def app(anyio_backend: Any) -> AsyncGenerator[App, None]:  # noqa: ARG001
    nonebot.require("nonebot_plugin_exe_code")

    from nonebot_plugin_orm import init_orm

    from nonebot_plugin_exe_code.constant import DATA_DIR

    exist_file = {i.name for i in DATA_DIR.iterdir()}
    await init_orm()

    yield App()

    for fp in DATA_DIR.iterdir():
        if fp.name not in exist_file:
            fp.unlink()


@pytest.fixture(scope="session", autouse=True)
def _load_adapter() -> None:
    # 加载适配器
    driver = nonebot.get_driver()
    driver.register_adapter(console.Adapter)
    driver.register_adapter(onebot.v11.Adapter)
    driver.register_adapter(qq.Adapter)
    driver.register_adapter(satori.Adapter)
    driver.register_adapter(telegram.Adapter)
