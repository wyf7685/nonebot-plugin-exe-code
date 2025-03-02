from collections.abc import Callable
from typing import Any, ClassVar, Self, override

import anyio
from nonebot.adapters import Adapter, Bot, Event, Message, MessageSegment
from nonebot_plugin_alconna.uniseg import Receipt, Target, UniMessage, reply_fetch
from nonebot_plugin_session import Session, SessionIdType
from nonebot_plugin_waiter import prompt as waiter_prompt

from ..exception import BotEventMismatch, NoMethodDescription
from ..typings import T_ConstVar, T_Context, T_Message, is_message_t
from .decorators import debug_log, export, strict
from .group import Group
from .help_doc import descript, message_alia
from .interface import Interface
from .user import User
from .user_const_var import get_default_context, load_const, set_const
from .utils import (
    Buffer,
    as_msg,
    as_unimsg,
    export_message,
    export_superuser,
    get_method_description,
    is_export_method,
    is_super_user,
    send_message,
)

api_registry: dict[type[Adapter], type["API"]] = {}
message_alia(Message, MessageSegment)


def register_api[A: type["API"]](adapter: type[Adapter]) -> Callable[[A], A]:
    def decorator(api: A) -> A:
        api_registry[adapter] = api
        adapter_name = adapter.get_name()
        for desc in api.__method_description__.values():
            desc.description = f"[{adapter_name}] {desc.description}"
        return api

    return decorator


class API[B: Bot, E: Event](Interface):
    __inst_name__: ClassVar[str] = "api"
    __slots__ = ("__bot", "__event", "__session")

    def __init__(
        self,
        bot: B,
        event: E,
        session: Session,
        context: T_Context,
    ) -> None:
        if not self._validate(bot, event):
            raise BotEventMismatch("Bot/Event type mismatch")

        super().__init__(context)
        self.__bot = bot
        self.__event = event
        self.__session = session

    @property
    def bot(self) -> B:
        return self.__bot

    @property
    def event(self) -> E:
        return self.__event

    @property
    def session(self) -> Session:
        return self.__session

    @property
    def uid(self) -> str:
        return self.session.id1 or ""

    @property
    def gid(self) -> str | None:
        return self.session.id2

    @property
    def session_id(self) -> str:
        return self.session.get_id(SessionIdType.USER).replace(" ", "_")

    @property
    def mid(self) -> str | int:
        return UniMessage.get_message_id(self.event, self.bot)

    @classmethod
    def _validate(cls, bot: B, event: E) -> bool:
        return isinstance(bot, Bot) and isinstance(event, Event)

    @descript(
        description="获取当前平台类型",
        parameters=None,
        result="当前平台类型",
    )
    @debug_log
    async def get_platform(self) -> str:
        return self.bot.type

    @descript(
        description="获取当前消息的引用消息 ID",
        parameters=None,
        result="引用消息的 ID",
    )
    @export
    @debug_log
    async def reply_id(self) -> str | None:
        reply = await reply_fetch(self.event, self.bot)
        return reply and reply.id

    @descript(
        description="调用 bot.send 向当前会话发送平台消息",
        parameters=dict(
            msg="要发送的消息",
            kwds="任意额外参数",
        ),
        result="bot.send 的返回值",
    )
    @debug_log
    @strict
    async def native_send(
        self,
        msg: Any,
        **kwds: Any,
    ) -> Any:
        return await self.bot.send(
            event=self.event,
            message=await as_msg(msg),
            **kwds,
        )

    @descript(
        description="向用户ID为uid的用户发送私聊消息",
        parameters=dict(
            uid="需要发送私聊的用户ID",
            msg="发送的内容",
        ),
    )
    @debug_log
    @strict
    async def send_prv(self, uid: int | str, msg: T_Message) -> Receipt:
        return await send_message(
            session=self.session,
            target=Target.user(str(uid)),
            message=msg,
        )

    @descript(
        description="向群组ID为gid的群组发送消息",
        parameters=dict(
            gid="需要发送消息的群组ID",
            msg="发送的内容",
        ),
    )
    @debug_log
    @strict
    async def send_grp(self, gid: int | str, msg: T_Message) -> Receipt:
        return await send_message(
            session=self.session,
            target=Target.group(str(gid)),
            message=msg,
        )

    @descript(
        description="向当前会话发送消息",
        parameters=dict(msg="需要发送的消息"),
    )
    @export
    @debug_log
    async def feedback(self, msg: Any) -> Receipt:
        if not is_message_t(msg):
            msg = str(msg)

        return await send_message(
            session=self.session,
            target=None,
            message=msg,
        )

    @descript(
        description="获取用户对象",
        parameters=dict(uid="用户ID"),
        result="User对象",
    )
    @export
    @strict
    def user(self, uid: int | str) -> User[Self]:
        return User(self, str(uid))

    @descript(
        description="获取群聊对象",
        parameters=dict(gid="群组ID"),
        result="Group对象",
    )
    @export
    @strict
    def group(self, gid: int | str) -> Group[Self]:
        return Group(self, str(gid))

    @descript(
        description="判断当前会话是否为群聊",
        parameters=None,
        result="当前会话为群聊返回True，否则返回False",
    )
    @debug_log
    @strict
    def is_group(self) -> bool:
        return not UniMessage.get_target(self.event, self.bot).private

    @descript(
        description="设置环境常量，在每次执行代码时加载",
        parameters=dict(
            name="设置的环境变量名",
            value="设置的环境常量值，仅允许输入可被json序列化的对象，留空(None)则为删除",
        ),
    )
    @debug_log
    @strict
    def set_const(self, name: str, value: T_ConstVar = None) -> None:
        if value is None:
            set_const(self.session_id, name)
            return

        set_const(self.session_id, name, value)

    @export
    @debug_log
    def print(self, *args: Any, sep: str = " ", end: str = "\n", **_: Any) -> None:
        buffer = Buffer.get(self.session.get_id(1).replace(" ", "_"))
        buffer.write(str(sep).join(map(str, args)) + str(end))

    @export
    @debug_log
    @strict
    async def input(
        self,
        prompt: T_Message | None = None,
        timeout: float = 30,  # noqa: ASYNC109
    ) -> UniMessage:
        prompt = (
            await (await as_unimsg(prompt)).export(self.bot)
            if prompt is not None
            else ""
        )
        if result := await waiter_prompt(prompt, timeout=timeout):
            return await UniMessage.generate(message=result)
        raise TimeoutError("input 超时")

    @descript(
        description="向当前会话发送 API 说明",
        parameters=dict(method="需要获取帮助的函数"),
    )
    @export
    @debug_log
    @strict
    async def help(self, method: Callable[..., Any]) -> None:
        desc = get_method_description(method)
        if desc is None:
            raise NoMethodDescription(method=method)
        text = desc.format()
        if not is_export_method(method):
            text = f"{desc.inst_name}.{text}"
        await self.feedback(UniMessage.text(text))

    @descript(
        description="在执行代码时等待",
        parameters=dict(seconds="等待的时间，单位秒"),
    )
    @export
    @debug_log
    @strict
    async def sleep(self, seconds: int | float) -> None:  # noqa: PYI041
        await anyio.sleep(seconds)

    @descript(
        description="重置环境",
        parameters=None,
    )
    @export
    @debug_log
    def reset(self) -> None:
        from ..context import Context

        context = Context.get_context(self.session).ctx
        context.clear()
        context.update(get_default_context())
        self.export()

    @override
    def export(self) -> None:
        super().export()

        for k, v in load_const(self.session_id).items():
            self._export(k, v)
        self._export("uid", self.uid)
        self._export("qid", self.uid)
        self._export("gid", self.gid)
        for k, v in export_message(self.bot.adapter):
            self._export(k, v)

        if is_super_user(self.bot, self.uid):
            for k, v in export_superuser():
                self._export(k, v)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} user_id={self.uid}>"
