import contextlib
import inspect
from asyncio import Future, Queue, Task, get_event_loop
from collections.abc import AsyncGenerator
from copy import deepcopy
from typing import Any, ClassVar, cast

import nonebot
from nonebot.adapters import Bot, Event, Message
from nonebot.internal.matcher import current_bot, current_event
from nonebot.utils import escape_tag
from nonebot_plugin_alconna.uniseg import Image, UniMessage
from nonebot_plugin_session import Session, SessionIdType, extract_session
from typing_extensions import Self

from .interface import API, Buffer, default_context, get_api_class
from .typings import T_Context, T_Executor

logger = nonebot.logger.opt(colors=True)

EXECUTOR_INDENT = " " * 8
EXECUTOR_FUNCTION = """\
last_exc, __exception__ = __exception__,  (None, None)
async def __executor__():
    try:
        {CODE}
    except BaseException as e:
        global __exception__
        __exception__ = (e, __import__("traceback").format_exc())
    finally:
        globals().update({
            k: v for k, v in dict(locals()).items()
            if not k.startswith("__") and not k.endswith("__")
        })
"""


class Context:
    __ua2session: ClassVar[dict[tuple[str, str], Session]] = {}
    __contexts: ClassVar[dict[str, Self]] = {}

    uin: str
    ctx: T_Context
    locked: bool
    waitlist: Queue[Future[None]]
    task: Task[Any] | None

    def __init__(self, uin: str) -> None:
        self.uin = uin
        self.ctx = deepcopy(default_context)
        self.locked = False
        self.waitlist = Queue()
        self.task = None

    @classmethod
    def _session2uin(cls, session: Session | Event | str) -> str:
        if isinstance(session, Event):
            if current_event.get() is not session:
                raise RuntimeError("event mismatch")
            key = (session.get_user_id(), current_bot.get().type)
            if key not in cls.__ua2session:
                raise RuntimeError(f"session {key!r} not initialized")
            session = cls.__ua2session[key]
        elif isinstance(session, str):
            key = (session, current_bot.get().type)
            if key not in cls.__ua2session:
                raise RuntimeError(f"session {key!r} not initialized")
            session = cls.__ua2session[key]

        key = (session.id1 or "", session.bot_type)
        if key not in cls.__ua2session:
            cls.__ua2session[key] = session.model_copy()

        return session.get_id(SessionIdType.USER).replace(" ", "_")

    @classmethod
    def get_context(cls, session: Session | Event | str) -> Self:
        uin = cls._session2uin(session)
        if uin not in cls.__contexts:
            logger.debug(f"为用户 <y>{uin}</y> 创建 Context")
            cls.__contexts[uin] = cls(uin)

        return cls.__contexts[uin]

    @contextlib.asynccontextmanager
    async def lock(self) -> AsyncGenerator[None, None]:
        fut: Future[None]

        if self.locked:
            fut = get_event_loop().create_future()
            await self.waitlist.put(fut)
            await fut
        self.locked = True

        try:
            yield
        finally:
            if not self.waitlist.empty():
                fut = await self.waitlist.get()
                fut.set_result(None)
            self.locked = False
            self.task = None

    def _solve_code(self, raw_code: str, api: API) -> T_Executor:
        assert self.locked, "`Context._solve_code` called without lock"

        # 预处理代码
        lines: list[str] = [
            f"global {', '.join(self.ctx.keys())}",
            *raw_code.split("\n"),
        ]
        solved = EXECUTOR_FUNCTION.replace("{CODE}", f"\n{EXECUTOR_INDENT}".join(lines))
        code = compile(solved, f"<executor_{self.uin}>", "exec")

        # 包装为异步函数
        exec(code, self.ctx, self.ctx)  # noqa: S102
        executor = self.ctx.pop("__executor__")

        if inspect.isasyncgenfunction(executor):
            _executor = executor

            async def executor() -> None:
                try:
                    async for value in _executor():
                        await api.feedback(repr(value))
                except BaseException as err:
                    import traceback

                    self.ctx["last_exc"] = self.ctx["__exception__"]
                    self.ctx["__exception__"] = (err, traceback.format_exc())

        return executor

    @classmethod
    async def execute(cls, bot: Bot, event: Event, code: str) -> None:
        session = extract_session(bot, event)
        uin = cls._session2uin(session)
        self = cls.get_context(session)
        api_class = get_api_class(bot)
        colored_uin = f"<y>{escape_tag(uin)}</y>"

        # 执行代码时加锁，避免出现多段代码分别读写变量
        async with self.lock(), api_class(bot, event, session, self.ctx) as api:
            executor = self._solve_code(code, api)
            escaped = escape_tag(repr(executor))
            logger.debug(f"为用户 {colored_uin} 创建 executor: {escaped}")

            self.task = get_event_loop().create_task(executor())
            result, self.task = await self.task, None

            if buf := Buffer.get(uin).read().rstrip("\n"):
                logger.debug(f"用户 {colored_uin} 清空缓冲:")
                logger.opt(raw=True).debug(buf)
                await UniMessage.text(buf).send()

            if result is not None:
                result = repr(result)
                logger.debug(f"用户 {colored_uin} 输出返回值: {escape_tag(result)}")
                await UniMessage.text(result).send()

        # 处理异常
        if exc := self.ctx.setdefault("__exception__", (None, None))[0]:
            raise cast(Exception, exc)

    def cancel(self) -> bool:
        if self.task is None:
            return False
        return self.task.cancel()

    def set_value(self, varname: str, value: Any) -> None:
        if value is not None:
            self.ctx[varname] = value
        elif varname in self.ctx:
            del self.ctx[varname]

    def set_gem(self, msg: Message) -> None:
        self.set_value("gem", msg)

    def set_gurl(self, msg: UniMessage[Image] | Image) -> None:
        url: str | None = None
        if isinstance(msg, UniMessage) and msg.has(Image):
            url = msg[Image, 0].url
        elif isinstance(msg, Image):
            url = msg.url
        self.set_value("gurl", url)

    def __getitem__(self, key: str, /) -> Any:
        return self.ctx[key]

    def __setitem__(self, key: str, value: Any, /) -> None:
        self.ctx[key] = value

    def __delitem__(self, key: str, /) -> None:
        del self.ctx[key]
