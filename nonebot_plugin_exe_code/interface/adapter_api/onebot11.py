import asyncio
import contextlib
import functools
import uuid
from base64 import b64encode
from datetime import timedelta
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

from nonebot import on_fullmatch, on_message
from nonebot.log import logger
from typing_extensions import override

from ..api import API as BaseAPI
from ..api import register_api
from ..help_doc import descript
from ..utils import Result, debug_log, export
from ._send_ark import SendArk

if TYPE_CHECKING:

    class _ApiCall(Protocol):
        async def __call__(self, **kwargs: Any) -> Any: ...


def file2str(file: str | bytes | BytesIO | Path) -> str:
    if isinstance(file, BytesIO):
        file = file.getvalue()
    if isinstance(file, Path):
        file = file.resolve().read_bytes()
    if isinstance(file, bytes):
        file = f"base64://{b64encode(file).decode()}"
    return file


with contextlib.suppress(ImportError):
    from nonebot.adapters.onebot.v11 import (
        ActionFailed,
        Adapter,
        Message,
        MessageSegment,
        PrivateMessageEvent,
    )

    logger = logger.opt(colors=True)

    async def create_ark_card(api: "API", ark: "MessageArk") -> MessageSegment:
        raise NotImplementedError

    with contextlib.suppress(ImportError, RuntimeError):
        from nonebot import get_plugin_config
        from nonebot.adapters.qq import Bot as QQBot
        from nonebot.adapters.qq import C2CMessageCreateEvent
        from nonebot.adapters.qq import MessageSegment as QQMS  # noqa: N814
        from nonebot.adapters.qq.models import MessageArk
        from pydantic import BaseModel

        class Config(BaseModel):
            class ExeCodeConfig(BaseModel):
                qbot_id: int = 0
                qbot_timeout: float = 30.0

            exe_code: ExeCodeConfig = ExeCodeConfig()

        _conf = get_plugin_config(Config).exe_code
        if not _conf.qbot_id:  # pragma: no cover
            logger.warning("官方机器人QQ账号未配置，ark卡片将不可用")
            raise RuntimeError

        async def create_ark_card(
            api: "API",
            ark: MessageArk,
        ) -> MessageSegment:
            loop = asyncio.get_running_loop()
            future: asyncio.Future[str] = loop.create_future()

            key = f"$ARK-{uuid.uuid4()}$"
            logger.debug(f"生成 ark key: {key}")

            async def handle_qq(bot: QQBot, event: C2CMessageCreateEvent) -> None:
                logger.debug("QQ Adapter 收到 ark key")
                try:
                    await bot.send(event, QQMS.ark(ark))
                    logger.debug("QQ Adapter 已发送 ark 消息成功")
                except Exception as err:
                    logger.debug(f"QQ Adapter 发送 ark 消息失败: {err!r}")
                    if not future.done():
                        future.set_exception(err)

            def rule(event: PrivateMessageEvent) -> bool:
                return event.user_id == _conf.qbot_id and len(event.message) == 1

            async def handle_ob(event: PrivateMessageEvent) -> None:
                seg = event.message.include("json")[0]
                logger.debug("OneBot V11 Adapter 收到 ark 卡片")
                card_json = seg.data["data"]
                if not future.done():
                    future.set_result(card_json)
                    logger.debug(f"OneBot V11 Adapter 设置 future 结果: {card_json}")

            expire = timedelta(seconds=_conf.qbot_timeout)
            matchers = {
                on_fullmatch(key, handlers=[handle_qq], temp=True, expire_time=expire),
                on_message(rule, handlers=[handle_ob], temp=True, expire_time=expire),
            }

            def cleanup() -> None:  # pragma: no cover
                for matcher in matchers:
                    with contextlib.suppress(ValueError):
                        matcher.destroy()

                if not future.done():
                    future.set_exception(TimeoutError("卡片获取超时"))

            await api.send_prv(_conf.qbot_id, key)
            loop.call_later(_conf.qbot_timeout, cleanup)
            card_json = await future
            logger.debug("API 调用结束, 获得 card_json")
            return MessageSegment.json(card_json)

    @register_api(Adapter)
    class API(SendArk, BaseAPI):
        @descript(
            description="调用 OneBot V11 接口",
            parameters=dict(
                api=(
                    "需要调用的接口名，参考 "
                    "https://github.com/botuniverse/onebot-11/blob/master/api/public.md"
                ),
                data="以命名参数形式传入的接口调用参数",
            ),
            ignore={"raise_text"},
        )
        @debug_log
        async def call_api(
            self,
            api: str,
            *,
            raise_text: str | None = None,
            **data: Any,
        ) -> Result:
            res: dict[str, Any] | list[Any] | None = None
            try:
                res = await self.bot.call_api(api, **data)
            except ActionFailed as e:
                res = {"error": e}
            except BaseException as e:
                res = {"error": e}
                msg = f"用户({self.qid})调用api<y>{api}</y>时发生错误: <r>{e}</r>"
                logger.opt(exception=e).warning(msg)

            if isinstance(res, dict):
                res.setdefault("error", None)

            result = Result(res)
            if result.error is not None and raise_text is not None:
                raise RuntimeError(raise_text) from result.error
            return result

        def __getattr__(self, name: str) -> "_ApiCall":
            if name.startswith("__") and name.endswith("__"):
                raise AttributeError(
                    f"'{self.__class__.__name__}' object has no attribute '{name}'"
                )
            return functools.partial(self.call_api, name)

        @export
        @descript(
            description="撤回指定消息",
            parameters=dict(msg_id="需要撤回的消息ID，可通过Result/getmid获取"),
        )
        @debug_log
        async def recall(self, msg_id: int) -> Result:
            logger.debug(f"[OneBot V11] 撤回消息: {msg_id=}")
            return await self.call_api(
                "delete_msg",
                message_id=msg_id,
                raise_text="撤回消息失败",
            )

        @export
        @descript(
            description="通过消息ID获取指定消息",
            parameters=dict(msg_id="需要获取的消息ID，可通过getmid获取"),
            result="获取到的消息",
        )
        @debug_log
        async def get_msg(self, msg_id: int) -> Message:
            logger.debug(f"[OneBot V11] 获取消息: {msg_id=}")
            res = await self.call_api(
                "get_msg",
                message_id=msg_id,
                raise_text="获取消息失败",
            )
            return Message(res["raw_message"])

        @export
        @descript(
            description="通过合并转发ID获取合并转发消息",
            parameters=dict(msg_id="需要获取的合并转发ID，可通过getcqcode获取"),
            result="获取到的合并转发消息列表",
        )
        @debug_log
        async def get_fwd(self, msg_id: int) -> list[Message]:
            logger.debug(f"[OneBot V11] 获取合并转发消息: {msg_id=}")
            res = await self.call_api(
                "get_forward_msg",
                message_id=msg_id,
                raise_text="获取合并转发消息失败",
            )
            return [Message(i["raw_message"]) for i in res["messages"]]

        @descript(
            description="[NapCat] 发送带有外显文本的图片",
            parameters=dict(
                summary="外显文本",
                url="图片链接，默认为当前环境gurl",
            ),
        )
        @debug_log
        async def img_summary(self, summary: str, url: str | None = None) -> None:
            if url is None:
                from ...context import Context

                url = Context.get_context(self.session).ctx.get("gurl")

            if not url:
                raise ValueError("无效 url")

            logger.debug(f"[NapCat] 创建图片外显: <y>{summary}</y>, <c>{url}</c>")
            seg = MessageSegment.image(url)
            seg.data["summary"] = summary
            await self._native_send(Message(seg))

        @descript(
            description="设置群名片",
            parameters=dict(
                card="新的群名片",
                qid="被设置者QQ号, 默认为当前用户",
                gid="所在群号, 默认为当前群聊, 私聊时必填",
            ),
        )
        @debug_log
        async def set_card(
            self,
            card: str,
            qid: str | int | None = None,
            gid: str | int | None = None,
        ) -> None:
            if gid is None and self.gid is None:
                raise ValueError("未指定群号")
            await self.call_api(
                "set_group_card",
                group_id=int(gid or self.gid or 0),
                user_id=int(qid or self.qid),
                card=str(card),
            )

        @descript(
            description="设置群禁言",
            parameters=dict(
                duration="禁言时间, 单位秒, 填0为解除禁言",
                qid="被禁言者QQ号",
                gid="所在群号, 默认为当前群聊, 私聊时必填",
            ),
        )
        @debug_log
        async def set_mute(
            self, duration: float, qid: str | int, gid: str | int | None = None
        ) -> None:
            if gid is None and self.gid is None:
                raise ValueError("未指定群号")
            await self.call_api(
                "set_group_ban",
                group_id=int(gid or self.gid or 0),
                user_id=int(qid),
                duration=float(duration),
            )

        @descript(
            description="资料卡点赞，需要机器人好友",
            parameters=dict(
                times="点赞次数，非vip机器人每天上限10次",
                qid="点赞QQ号, 默认为当前用户",
            ),
        )
        @debug_log
        async def send_like(self, times: int, qid: str | int | None = None) -> None:
            await self.call_api("send_like", user_id=int(qid or self.qid), times=times)

        @descript(
            description="发送群文件",
            parameters=dict(
                file="需要发送的文件，可以是url/base64/bytes/Path",
                name="上传的文件名",
                gid="目标群号，默认为当前群聊，私聊时必填",
            ),
        )
        @debug_log
        async def send_group_file(
            self,
            file: str | bytes | BytesIO | Path,
            name: str,
            gid: str | int | None = None,
        ) -> None:
            file = file2str(file)
            gid = gid or self.gid
            if gid is None:
                raise ValueError("未指定群号")
            if not str(gid).isdigit():
                raise ValueError(f"群号错误: {gid} 不是数字")

            # https://docs.go-cqhttp.org/api/#%E4%B8%8A%E4%BC%A0%E7%BE%A4%E6%96%87%E4%BB%B6
            await self.call_api(
                "upload_group_file",
                group_id=int(gid),
                file=file,
                name=name,
            )

        @descript(
            description="发送私聊文件",
            parameters=dict(
                file="需要发送的文件，可以是url/base64/bytes/Path",
                name="上传的文件名",
                qid="目标QQ号，默认为当前用户",
            ),
        )
        @debug_log
        async def send_private_file(
            self,
            file: str | bytes | BytesIO | Path,
            name: str,
            qid: str | int | None = None,
        ) -> None:
            file = file2str(file)
            qid = qid or self.qid
            if not str(qid).isdigit():
                raise ValueError(f"QQ号错误: {qid} 不是数字")

            # https://docs.go-cqhttp.org/api/#%E4%B8%8A%E4%BC%A0%E7%A7%81%E8%81%8A%E6%96%87%E4%BB%B6
            await self.call_api(
                "upload_private_file",
                user_id=int(qid),
                file=file,
                name=name,
            )

        @descript(
            description="向当前会话发送文件",
            parameters=dict(
                file="需要发送的文件，可以是url/base64/bytes/Path",
                name="上传的文件名",
            ),
        )
        @debug_log
        async def send_file(
            self,
            file: str | bytes | BytesIO | Path,
            name: str,
        ) -> None:
            if self.is_group():
                await self.send_group_file(file, name, self.gid)
            else:
                await self.send_private_file(file, name, self.qid)

        @override
        async def _send_ark(self, ark: "MessageArk") -> Any:
            card = Message(await create_ark_card(self, ark))
            return await self._native_send(card)
