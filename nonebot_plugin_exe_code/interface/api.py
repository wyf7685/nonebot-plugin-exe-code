import asyncio
import json
from typing import Any, ClassVar, override

from nonebot.adapters import Adapter, Bot, Event, Message, MessageSegment
from nonebot.internal.matcher import current_event
from nonebot.log import logger
from nonebot_plugin_alconna.uniseg import Receipt, Target, UniMessage
from nonebot_plugin_session import Session
from nonebot_plugin_waiter import prompt as waiter_prompt

from ..constant import (
    INTERFACE_METHOD_DESCRIPTION,
    T_Context,
    T_ForwardMsg,
    T_Message,
    T_OptConstVar,
)
from .group import Group
from .help_doc import FuncDescription, descript, message_alia
from .interface import Interface
from .user import User
from .user_const_var import default_context, load_const, set_const
from .utils import (
    Buffer,
    as_unimsg,
    debug_log,
    export,
    export_manager,
    is_export_method,
    is_message_t,
    is_super_user,
    send_forward_message,
    send_message,
)

logger = logger.opt(colors=True)
api_registry: dict[type[Adapter], type["API"]] = {}
message_alia(Message, MessageSegment)


def register_api(adapter: type[Adapter]):

    def decorator(api: type["API"]) -> type["API"]:
        api_registry[adapter] = api
        adapter_name = adapter.get_name()
        for desc in api.__method_description__.values():
            desc.description = f"[{adapter_name}] {desc.description}"
        return api

    return decorator


class API(Interface):
    __inst_name__: ClassVar[str] = "api"

    bot: Bot
    qid: str
    gid: str | None
    session: Session
    event: Event

    def __init__(self, bot: Bot, session: Session) -> None:
        super().__init__()
        self.bot = bot
        self.qid = session.id1 or ""
        self.gid = session.id2
        self.session = session
        self.event = current_event.get()

    async def _native_send(self, msg: str | Message | MessageSegment) -> Any:
        return await self.bot.send(self.event, msg)

    @descript(
        description="向QQ号为qid的用户发送私聊消息",
        parameters=dict(
            qid="需要发送私聊的QQ号",
            msg="发送的内容",
        ),
    )
    @debug_log
    async def send_prv(self, qid: int | str, msg: T_Message) -> Receipt:
        return await send_message(
            session=self.session,
            target=Target.user(str(qid)),
            message=msg,
        )

    @descript(
        description="向群号为gid的群聊发送消息",
        parameters=dict(
            gid="需要发送消息的群号",
            msg="发送的内容",
        ),
    )
    @debug_log
    async def send_grp(self, gid: int | str, msg: T_Message) -> Receipt:
        return await send_message(
            session=self.session,
            target=Target.group(str(gid)),
            message=msg,
        )

    @descript(
        description="向QQ号为qid的用户发送合并转发消息",
        parameters=dict(
            qid="需要发送消息的QQ号",
            msgs="发送的消息列表",
        ),
        result="Receipt",
    )
    @debug_log
    async def send_prv_fwd(self, qid: int | str, msgs: T_ForwardMsg) -> Receipt:
        return await send_forward_message(
            session=self.session,
            target=Target.group(str(qid)),
            msgs=msgs,
        )

    @descript(
        description="向群号为gid的群聊发送合并转发消息",
        parameters=dict(
            gid="需要发送消息的群号",
            msgs="发送的消息列表",
        ),
    )
    @debug_log
    async def send_grp_fwd(self, gid: int | str, msgs: T_ForwardMsg) -> Receipt:
        return await send_forward_message(
            session=self.session,
            target=Target.group(str(gid)),
            msgs=msgs,
        )

    @export
    @descript(
        description="向当前会话发送合并转发消息",
        parameters=dict(msgs="发送的消息列表"),
    )
    @debug_log
    async def send_fwd(self, msgs: T_ForwardMsg) -> Receipt:
        return await send_forward_message(
            session=self.session,
            target=None,
            msgs=msgs,
        )

    @export
    @descript(
        description="向当前会话发送消息",
        parameters=dict(
            msg="需要发送的消息",
            fwd="传入的是否为合并转发消息列表",
        ),
    )
    @debug_log
    async def feedback(self, msg: Any, fwd: bool = False) -> Receipt:
        if isinstance(msg, list):
            if fwd and all(is_message_t(i) for i in msg):
                return await self.send_fwd(msg)

        if not is_message_t(msg):
            msg = str(msg)

        return await send_message(
            session=self.session,
            target=None,
            message=msg,
        )

    @export
    @descript(
        description="获取用户对象",
        parameters=dict(qid="用户QQ号"),
        result="User对象",
    )
    def user(self, qid: int | str) -> "User":
        return User(self, str(qid))

    @export
    @descript(
        description="获取群聊对象",
        parameters=dict(gid="群号"),
        result="Group对象",
    )
    def group(self, gid: int | str) -> "Group":
        return Group(self, str(gid))

    @descript(
        description="判断当前会话是否为群聊",
        parameters=None,
        result="当前会话为群聊返回True，否则返回False",
    )
    @debug_log
    def is_group(self) -> bool:
        return not UniMessage.get_target().private

    @descript(
        description="设置环境常量，在每次执行代码时加载",
        parameters=dict(
            name="设置的环境变量名",
            value="设置的环境常量值，仅允许输入可被json序列化的对象，留空(None)则为删除",
        ),
    )
    @debug_log
    def set_const(self, name: str, value: T_OptConstVar = None) -> None:
        if value is None:
            set_const(self.qid, name)
            return

        try:
            json.dumps([value])
        except ValueError as e:
            raise TypeError("设置常量的类型必须是可被json序列化的对象") from e

        set_const(self.qid, name, value)

    @export
    @debug_log
    def print(self, *args: Any, sep: str = " ", end: str = "\n", **_):
        Buffer.get(self.qid).write(str(sep).join(map(str, args)) + str(end))

    @export
    @debug_log
    async def input(
        self,
        prompt: T_Message = "",
        timeout: float = 30,
    ) -> UniMessage:
        prompt = await (await as_unimsg(prompt)).export() if prompt else ""
        if result := await waiter_prompt(prompt, timeout=timeout):
            return await UniMessage.generate(message=result)
        raise TimeoutError("input 超时")

    @export
    @descript(
        description="向当前会话发送API说明",
        parameters=dict(method="需要获取帮助的函数，留空则为完整文档"),
    )
    @debug_log
    async def help(self, method: Any = ...) -> Receipt:
        if method is not ...:
            desc: FuncDescription = getattr(method, INTERFACE_METHOD_DESCRIPTION)
            text = desc.format(method)
            if not is_export_method(method):
                text = f"{self.__inst_name__}.{text}"
            return await self.feedback(text)

        content, description = self._get_all_description()
        msgs: list[T_Message] = [
            "   ===== API说明 =====   ",
            " - API说明文档 - 目录 - \n" + "\n".join(content),
            *description,
        ]
        return await self.send_fwd(msgs)

    @export
    @descript(
        description="在执行代码时等待",
        parameters=dict(seconds="等待的时间，单位秒"),
    )
    @debug_log
    async def sleep(self, seconds: float) -> None:
        await asyncio.sleep(seconds)

    @export
    @descript(
        description="重置环境",
        parameters=None,
    )
    @debug_log
    def reset(self) -> None:
        from ..context import Context

        context = Context.get_context(self.session).ctx
        context.clear()
        context.update(default_context)
        self.export_to(context)

    @override
    def export_to(self, context: T_Context) -> None:
        super().export_to(context)

        context.update(load_const(self.qid))
        context["qid"] = self.qid
        context["gid"] = self.gid

        if is_super_user(self.bot, self.qid):
            export_manager(context)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(user_id={self.qid})"
