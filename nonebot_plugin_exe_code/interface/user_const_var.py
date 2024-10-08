import json
from pathlib import Path
from typing import Any

from nonebot_plugin_alconna.uniseg import At, Image, Reply, Text, UniMessage

from ..constant import DATA_DIR
from ..typings import T_ConstVar, T_Context, UserStr

default_context: T_Context = {}


def context_var(item: Any, name: str | None = None) -> None:
    key = name or getattr(item, "__name__", None)
    assert key is not None, f"Name for {item!r} cannot be empty"
    default_context[key] = item


context_var((None, None), "__exception__")
context_var(lambda x: At(flag="user", target=str(x)), "At")
context_var(lambda x: Reply(id=str(x)), "Reply")
[context_var(i) for i in {Image, Text, UniMessage, UserStr}]


def _const_var_path(uin: str) -> Path:
    fp = DATA_DIR / f"{uin}.json"
    if not fp.exists():
        fp.write_text("{}")
    return fp


def set_const(uin: str, name: str, value: T_ConstVar = None) -> None:
    if not name.isidentifier():
        raise ValueError(f"{name!r} 不是合法的 Python 标识符")

    fp = _const_var_path(uin)
    data = json.loads(fp.read_text())
    if value is not None:
        data[name] = value
    elif name in data:
        del data[name]
    fp.write_text(json.dumps(data))


def load_const(uin: str) -> dict[str, T_ConstVar]:
    return json.loads(_const_var_path(uin).read_text())
