import asyncio
import contextlib
import functools
import uuid
from datetime import timedelta
from typing import TYPE_CHECKING, Any, Protocol, override

from nonebot import on_fullmatch, on_message
from nonebot.log import logger

from ...constant import T_Context
from ..api import API as BaseAPI
from ..api import register_api
from ..help_doc import descript, message_alia
from ..utils import Result, debug_log, export
from .send_ark import SendArk

if TYPE_CHECKING:

    class _ApiCall(Protocol):
        async def __call__(self, **kwargs: Any) -> Any: ...


with contextlib.suppress(ImportError):
    from nonebot.adapters.onebot.v11 import (
        ActionFailed,
        Adapter,
        Message,
        MessageSegment,
        PrivateMessageEvent,
    )

    logger = logger.opt(colors=True)
    message_alia(Message, MessageSegment)

    async def create_ark_card(api: "API", ark: "MessageArk") -> MessageSegment:
        raise NotImplementedError

    with contextlib.suppress(ImportError, RuntimeError):
        from nonebot import get_plugin_config
        from nonebot.adapters.qq import Bot as QQBot
        from nonebot.adapters.qq import C2CMessageCreateEvent
        from nonebot.adapters.qq import MessageSegment as QQMS
        from nonebot.adapters.qq.models import MessageArk
        from pydantic import BaseModel

        class Config(BaseModel):
            class ExeCodeConfig(BaseModel):
                qbot_id: int = 0
                qbot_timeout: float = 30.0

            exe_code: ExeCodeConfig = ExeCodeConfig()

        _conf = get_plugin_config(Config).exe_code
        if not _conf.qbot_id:
            logger.warning("官方机器人QQ账号未配置，ark卡片将不可用")
            raise RuntimeError

        async def create_ark_card(
            api: "API",
            ark: MessageArk,
        ) -> MessageSegment:
            loop = asyncio.get_running_loop()
            future: asyncio.Future[str] = loop.create_future()

            key = f"$ARK-{uuid.uuid4()}$"

            async def handle_qq(bot: QQBot, event: C2CMessageCreateEvent):
                try:
                    await bot.send(event, QQMS.ark(ark))
                except Exception as err:
                    if not future.done():
                        future.set_exception(err)

            def rule(event: PrivateMessageEvent):
                return event.user_id == _conf.qbot_id and len(event.message) == 1

            async def handle_ob(event: PrivateMessageEvent):
                card_json = event.message.include("json")[0].data["data"]
                if not future.done():
                    future.set_result(card_json)

            expire = timedelta(seconds=_conf.qbot_timeout)
            matchers = {
                on_fullmatch(key, handlers=[handle_qq], temp=True, expire_time=expire),
                on_message(rule, handlers=[handle_ob], temp=True, expire_time=expire),
            }

            def cleanup() -> None:
                for matcher in matchers:
                    with contextlib.suppress(ValueError):
                        matcher.destroy()

                if not future.done():
                    future.set_exception(TimeoutError("卡片获取超时"))

            await api.send_prv(_conf.qbot_id, key)
            loop.call_later(_conf.qbot_timeout, cleanup)
            return MessageSegment.json(await future)

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

            seg = MessageSegment.image(url)
            seg.data["summary"] = summary
            await self._native_send(Message(seg))

        @override
        def export_to(self, context: T_Context) -> None:
            super().export_to(context)
            context["Message"] = Message
            context["MessageSegment"] = MessageSegment

        @override
        async def _send_ark(self, ark: "MessageArk") -> Any:
            card = Message(await create_ark_card(self, ark))
            return await self._native_send(card)
