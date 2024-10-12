import contextlib
from typing import Any, ClassVar

import nonebot

from ..help_doc import descript
from ..interface import Interface
from ..utils import debug_log

logger = nonebot.logger.opt(colors=True)


def build_ark(
    template_id: int,
    data: dict[str, str | list[dict[str, str]]],
) -> "MessageArk":
    raise NotImplementedError


with contextlib.suppress(ImportError):
    from nonebot.adapters.qq.models import (
        MessageArk,
        MessageArkKv,
        MessageArkObj,
        MessageArkObjKv,
    )

    # fmt: off
    def build_ark(
        template_id: int,
        data: dict[str, str | list[dict[str, str]]],
    ) -> MessageArk:
        logger.debug(f"构建 ark 结构体: {template_id=}, {data=!r}")
        return MessageArk(template_id=template_id, kv=[
            MessageArkKv(key=key, value=val)
            if isinstance(val, str) else
            MessageArkKv(key=key, obj=[
                MessageArkObj(obj_kv=[
                    MessageArkObjKv(key=k, value=v)
                    for k, v in okvd.items()
                ])
                for okvd in val
            ])
            for key, val in data.items()
        ])
    # fmt: on


class SendArk(Interface):
    """
    `SendArk` Mixin

    混入此类并实现 `_send_ark` 方法后，即可发送 ARK 卡片

    当前支持 ARK 模板: 23/24/37
    """

    __inst_name__: ClassVar[str] = "api"
    __slots__ = ()

    async def _send_ark(self, ark: "MessageArk") -> Any:
        raise NotImplementedError

    @descript(
        description="构建 ark 结构体",
        parameters=dict(
            template_id="ark模板id, 目前可为23/24/37",
            data="ark模板参数",
        ),
        result="ark结构体",
    )
    @debug_log
    def build_ark(
        self,
        template_id: int,
        data: dict[str, str | list[dict[str, str]]],
    ) -> "MessageArk":
        return build_ark(template_id, data)

    @descript(
        description="发送ark23卡片",
        parameters=dict(
            desc="描述文本",
            prompt="外显文本",
            lines="内容列表：str->纯文本，tuple[str,str]->跳转链接",
        ),
    )
    @debug_log
    async def ark_23(
        self,
        desc: str,
        prompt: str,
        lines: list[str | tuple[str, str]],
    ) -> None:
        ark = build_ark(
            template_id=23,
            data={
                "#DESC#": desc,
                "#PROMPT#": prompt,
                "#LIST#": [
                    {"desc": i} if isinstance(i, str) else {"desc": i[0], "link": i[1]}
                    for i in lines
                ],
            },
        )
        params = f"{desc=!r}, {prompt=!r}, {lines=!r}"
        logger.debug(f"发送 ark_23: {params}")
        await self._send_ark(ark)

    @descript(
        description="发送ark24卡片",
        parameters=dict(
            title="标题",
            desc="描述文本",
            prompt="外显文本",
            img="小图链接",
            link="跳转链接",
        ),
    )
    @debug_log
    async def ark_24(
        self,
        title: str,
        desc: str,
        prompt: str,
        img: str,
        link: str,
    ) -> None:
        ark = build_ark(
            template_id=24,
            data={
                "#TITLE#": title,
                "#METADESC#": desc,
                "#PROMPT#": prompt,
                "#IMG#": img,
                "#LINK#": link,
            },
        )
        params = f"{title=!r}, {desc=!r}, {prompt=!r}, {img=!r}, {link=!r}"
        logger.debug(f"发送 ark_24: {params}")
        await self._send_ark(ark)

    @descript(
        description="发送ark37卡片",
        parameters=dict(
            title="标题",
            subtitle="副标题",
            prompt="外显文本",
            img="图片链接",
            link="跳转链接",
        ),
    )
    @debug_log
    async def ark_37(
        self,
        title: str,
        subtitle: str,
        prompt: str,
        img: str,
        link: str,
    ) -> None:
        ark = build_ark(
            template_id=37,
            data={
                "#METATITLE#": title,
                "#METASUBTITLE#": subtitle,
                "#PROMPT#": prompt,
                "#METACOVER#": img,
                "#METAURL#": link,
            },
        )
        params = f"{title=!r}, {subtitle=!r}, {prompt=!r}, {img=!r}, {link=!r}"
        logger.debug(f"发送 ark_37: {params}")
        await self._send_ark(ark)
