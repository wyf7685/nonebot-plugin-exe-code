import asyncio
import contextlib
import functools
import uuid
from base64 import b64encode
from collections.abc import Callable
from datetime import timedelta
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, cast, overload, override

import nonebot
from nonebot import on_fullmatch, on_message
from nonebot.adapters import Event
from nonebot.utils import escape_tag

from ...typings import T_ForwardMsg, T_Message, UserStr
from ..api import API as BaseAPI
from ..api import register_api
from ..decorators import Overload, debug_log, export, strict
from ..group import Group as BaseGroup
from ..help_doc import descript
from ..user import User as BaseUser
from ..utils import Result, as_msg
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


async def _extract_user_str_args(us: UserStr) -> tuple[int, "Message", str | None]:
    user_id = int(us)
    args = us.extract_args()
    assert len(args) > 0
    content = cast("Message", await as_msg(args.pop(0)))
    name = None
    if args:
        name = (await as_msg(args.pop(0))).extract_plain_text()
    return user_id, content, name


async def convert_forward(msgs: T_ForwardMsg) -> "Message":
    from nonebot.adapters.onebot.v11 import Message, MessageSegment

    result = Message()
    for msg in msgs:
        if isinstance(msg, UserStr):
            user_id, content, name = await _extract_user_str_args(msg)
            result += MessageSegment.node_custom(
                user_id=user_id,
                nickname=name or "forward",
                content=content,
            )
        else:
            result += MessageSegment.node_custom(
                user_id=0,
                nickname="forward",
                content=cast("Message", await as_msg(msg)),
            )

    return result


with contextlib.suppress(ImportError):
    from nonebot.adapters.onebot.v11 import (
        ActionFailed,
        Adapter,
        Bot,
        Message,
        MessageEvent,
        MessageSegment,
        PrivateMessageEvent,
    )

    logger = nonebot.logger.opt(colors=True)

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

    class User(BaseUser["API"]):
        @descript(
            description="向用户发送私聊合并转发消息",
            parameters=dict(msgs="需要发送的消息列表"),
        )
        @debug_log
        @strict
        async def send_fwd(self, msgs: T_ForwardMsg) -> Result:
            return await self.api.send_prv_fwd(self.uid, msgs)

    class Group(BaseGroup["API"]):
        @descript(
            description="向群聊发送合并转发消息",
            parameters=dict(msgs="需要发送的消息列表"),
        )
        @debug_log
        @strict
        async def send_fwd(self, msgs: T_ForwardMsg) -> Result:
            return await self.api.send_grp_fwd(self.uid, msgs)

    @register_api(Adapter)
    class API(SendArk, BaseAPI[Bot, MessageEvent]):
        __slots__ = ()

        @classmethod
        @override
        def _validate(cls, bot: Bot, event: Event) -> bool:
            return isinstance(bot, Bot) and isinstance(event, MessageEvent)

        @descript(
            description="获取当前平台类型",
            parameters=None,
            result="当前平台类型",
        )
        @debug_log
        @override
        async def get_platform(self) -> str:
            data = await self.bot.get_version_info()
            return f"[{self.bot.type}] {data['app_name']} {data['app_version']}"

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
                res = await self.bot.call_api(
                    api,
                    **{k: v for k, v in data.items() if v is not None},
                )
            except ActionFailed as e:
                res = {"error": e}
            except BaseException as e:
                res = {"error": e}
                msg = (
                    f"用户(<c>{escape_tag(self.uid)}<c>) "
                    f"调用 api <y>{escape_tag(api)}</y> 时发生错误: "
                    f"<r>{escape_tag(repr(e))}</r>"
                )
                logger.opt(exception=e).warning(msg)

            if isinstance(res, dict):
                res.setdefault("error", None)

            result = Result(res)
            if result.error is not None and raise_text is not None:
                info = getattr(result.error, "info", {})
                info.setdefault("msg", raise_text)
                raise ActionFailed(**info) from result.error
            return result

        def __getattr__(self, name: str) -> "_ApiCall":
            if name.startswith("__") and name.endswith("__"):
                raise AttributeError(
                    f"'{self.__class__.__name__}' object has no attribute '{name}'"
                )
            return functools.partial(self.call_api, name)

        @descript(
            description="向用户ID为uid的用户发送合并转发消息",
            parameters=dict(
                uid="需要发送消息的用户ID",
                msgs="发送的消息列表",
            ),
        )
        @debug_log
        @strict
        async def send_prv_fwd(self, uid: int | str, msgs: T_ForwardMsg) -> Result:
            return await self.call_api(
                "send_private_forward_msg",
                user_id=int(uid),
                messages=await convert_forward(msgs),
            )

        @descript(
            description="向群号为gid的群聊发送合并转发消息",
            parameters=dict(
                gid="需要发送消息的群号",
                msgs="发送的消息列表",
            ),
        )
        @debug_log
        @strict
        async def send_grp_fwd(self, gid: int | str, msgs: T_ForwardMsg) -> Result:
            return await self.call_api(
                "send_group_forward_msg",
                user_id=int(gid),
                messages=await convert_forward(msgs),
            )

        @descript(
            description="向当前会话发送合并转发消息",
            parameters=dict(msgs="发送的消息列表"),
        )
        @export
        @debug_log
        @strict
        async def send_fwd(self, msgs: T_ForwardMsg) -> Result:
            if not self.is_group():
                return await self.send_prv_fwd(self.uid, msgs)
            if self.gid is not None:
                return await self.send_grp_fwd(self.gid, msgs)
            raise ValueError("获取消息上下文失败")  # pragma: no cover

        @overload
        async def help(self, method: Callable[..., Any]) -> None:
            await super().help(method)

        @overload
        async def help(self) -> None:
            content, description = self.get_all_description()
            msgs: list[T_Message] = [
                "   ===== API说明 =====   ",
                " - API说明文档 - 目录 - \n" + "\n".join(content),
                *description,
            ]
            await self.send_fwd(msgs)

        @Overload
        @descript(
            description="向当前会话发送API说明",
            parameters=dict(method="需要获取帮助的函数，留空则为合并转发的完整文档"),
        )
        @export
        @debug_log
        @override
        async def help(  # pyright: ignore[reportIncompatibleVariableOverride]
            self, method: Callable[..., Any] | None = None
        ) -> None: ...

        @descript(
            description="撤回指定消息",
            parameters=dict(msg_id="需要撤回的消息ID，可通过Result/getmid获取"),
        )
        @export
        @debug_log
        @strict
        async def recall(self, msg_id: int) -> Result:
            logger.debug(f"[OneBot V11] 撤回消息: {msg_id=}")
            return await self.call_api(
                "delete_msg",
                message_id=msg_id,
                raise_text="撤回消息失败",
            )

        @descript(
            description="通过消息ID获取指定消息",
            parameters=dict(msg_id="需要获取的消息ID，可通过getmid获取"),
            result="获取到的消息",
        )
        @export
        @debug_log
        @strict
        async def get_msg(self, msg_id: int) -> Message:
            logger.debug(f"[OneBot V11] 获取消息: {msg_id=}")
            res = await self.call_api(
                "get_msg",
                message_id=msg_id,
                raise_text="获取消息失败",
            )
            return Message(res["raw_message"])

        @descript(
            description="通过合并转发ID获取合并转发消息",
            parameters=dict(msg_id="需要获取的合并转发ID，可通过getcqcode获取"),
            result="获取到的合并转发消息列表",
        )
        @export
        @debug_log
        @strict
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
        @strict
        async def img_summary(self, summary: str, url: str | None = None) -> None:
            if url is None:
                from ...context import Context

                url = Context.get_context(self.session).ctx.get("gurl")

            if not url:
                raise ValueError("无效 url")

            logger.debug(f"[NapCat] 创建图片外显: <y>{summary}</y>, <c>{url}</c>")
            seg = MessageSegment.image(url)
            seg.data["summary"] = summary
            await self.native_send(Message(seg))

        @descript(
            description="设置群名片",
            parameters=dict(
                card="新的群名片",
                uid="被设置者用户ID, 默认为当前用户",
                gid="所在群号, 默认为当前群聊, 私聊时必填",
            ),
        )
        @debug_log
        @strict
        async def set_card(
            self,
            card: str,
            uid: str | int | None = None,
            gid: str | int | None = None,
        ) -> None:
            if gid is None and self.gid is None:
                raise ValueError("未指定群号")
            await self.call_api(
                "set_group_card",
                group_id=int(gid or self.gid or 0),
                user_id=int(uid or self.uid),
                card=str(card),
            )

        @descript(
            description="设置群禁言",
            parameters=dict(
                duration="禁言时间, 单位秒, 填0为解除禁言",
                uid="被禁言者用户ID",
                gid="所在群号, 默认为当前群聊, 私聊时必填",
            ),
        )
        @debug_log
        @strict
        async def set_mute(
            self,
            duration: int | float,  # noqa: PYI041
            uid: str | int,
            gid: str | int | None = None,
        ) -> None:
            if gid is None and self.gid is None:
                raise ValueError("未指定群号")
            await self.call_api(
                "set_group_ban",
                group_id=int(gid or self.gid or 0),
                user_id=int(uid),
                duration=float(duration),
            )

        @descript(
            description="资料卡点赞，需要机器人好友",
            parameters=dict(
                times="点赞次数，非vip机器人每天上限10次",
                uid="点赞用户ID, 默认为当前用户",
            ),
        )
        @debug_log
        @strict
        async def send_like(self, times: int, uid: str | int | None = None) -> None:
            await self.call_api("send_like", user_id=int(uid or self.uid), times=times)

        @descript(
            description="[NapCat/LLOneBot/Lagrange] 群聊消息回应",
            parameters=dict(
                emoji_id="回应的表情ID",
                message_id="需要回应的消息ID，可通过getmid获取",
                gid="[Lagrange] 指定群聊ID，默认为当前群聊",
            ),
        )
        @debug_log
        @strict
        async def set_reaction(
            self,
            emoji_id: str | int,
            message_id: str | int,
            gid: str | int | None = None,
        ) -> Result:
            platform = (await self.get_platform()).lower()
            if "napcat" in platform or "llonebot" in platform:
                # NapCat/LLOneBot
                return await self.call_api(
                    "set_msg_emoji_like",
                    message_id=int(message_id),
                    emoji_id=int(emoji_id),
                    raise_text="调用 NapCat/LLOneBot 接口 set_msg_emoji_like 出错",
                )

            if "lagrange" in platform:
                if (gid := gid or self.gid) is None:
                    raise TypeError("在 Lagrange 下进行表情回应需要指定群号")

                # Lagrange
                return await self.call_api(
                    "set_group_reaction",
                    group_id=int(gid),
                    message_id=int(message_id),
                    code=str(emoji_id),
                    raise_text="调用 Lagrange 接口 set_group_reaction 出错",
                )

            raise RuntimeError(f"发送消息回应失败: 未知平台 {platform}")

        @descript(
            description="发送群文件",
            parameters=dict(
                file="需要发送的文件，可以是url/base64/bytes/Path",
                name="上传的文件名",
                gid="目标群号，默认为当前群聊，私聊时必填",
                timeout="上传文件超时时长，单位秒",
            ),
        )
        @debug_log
        @strict
        async def send_group_file(
            self,
            file: str | bytes | BytesIO | Path,
            name: str,
            gid: str | int | None = None,
            timeout: float | None = None,  # noqa: ASYNC109
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
                _timeout=timeout,
            )

        @descript(
            description="发送私聊文件",
            parameters=dict(
                file="需要发送的文件，可以是url/base64/bytes/Path",
                name="上传的文件名",
                uid="目标用户ID，默认为当前用户",
                timeout="上传文件超时时长，单位秒",
            ),
        )
        @debug_log
        @strict
        async def send_private_file(
            self,
            file: str | bytes | BytesIO | Path,
            name: str,
            uid: str | int | None = None,
            timeout: float | None = None,  # noqa: ASYNC109
        ) -> None:
            file = file2str(file)
            uid = uid or self.uid
            if not str(uid).isdigit():
                raise ValueError(f"用户ID错误: {uid} 不是数字")

            # https://docs.go-cqhttp.org/api/#%E4%B8%8A%E4%BC%A0%E7%A7%81%E8%81%8A%E6%96%87%E4%BB%B6
            await self.call_api(
                "upload_private_file",
                user_id=int(uid),
                file=file,
                name=name,
                _timeout=timeout,
            )

        @descript(
            description="向当前会话发送文件",
            parameters=dict(
                file="需要发送的文件，可以是url/base64/bytes/Path",
                name="上传的文件名",
                timeout="上传文件超时时长，单位秒",
            ),
        )
        @debug_log
        @strict
        async def send_file(
            self,
            file: str | bytes | BytesIO | Path,
            name: str,
            timeout: float | None = None,  # noqa: ASYNC109
        ) -> None:
            if self.is_group():
                await self.send_group_file(file, name, self.gid, timeout)
            else:
                await self.send_private_file(file, name, self.uid, timeout)

        @override
        async def _send_ark(self, ark: "MessageArk") -> Any:
            card = Message(await create_ark_card(self, ark))
            return await self.native_send(card)

        @descript(
            description="获取用户对象",
            parameters=dict(uid="用户ID"),
            result="User对象",
        )
        @export
        @strict
        def user(  # pyright: ignore[reportIncompatibleVariableOverride]
            self, uid: int | str
        ) -> User:
            return User(self, str(uid))

        @descript(
            description="获取群聊对象",
            parameters=dict(gid="群号"),
            result="Group对象",
        )
        @export
        @strict
        def group(  # pyright: ignore[reportIncompatibleVariableOverride]
            self, gid: int | str
        ) -> Group:
            return Group(self, str(gid))
