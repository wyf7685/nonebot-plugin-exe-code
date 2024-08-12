import contextlib
from asyncio import Future, Queue, Task, get_event_loop
from copy import deepcopy
from typing import Any, ClassVar, cast
from typing_extensions import Self

from nonebot.adapters import Bot, Event, Message
from nonebot.log import logger
from nonebot_plugin_alconna.uniseg import Image, UniMessage
from nonebot_plugin_session import Session

from .constant import T_Context, T_Executor
from .interface import Buffer, default_context, get_api_class

logger = logger.opt(colors=True)

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
    _contexts: ClassVar[dict[str, Self]] = {}

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

    @staticmethod
    def _session2uin(session: Session | Event | str) -> str:
        if isinstance(session, Session):
            return session.id1 or "None"
        elif isinstance(session, Event):
            return session.get_user_id()
        else:
            return str(session)

    @classmethod
    def get_context(cls, session: Session | Event | str) -> Self:
        uin = cls._session2uin(session)
        if uin not in cls._contexts:
            logger.debug(f"为用户 <y>{uin}</y> 创建 Context")
            cls._contexts[uin] = cls(uin)

        return cls._contexts[uin]

    @contextlib.asynccontextmanager
    async def _lock(self):
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
            if self.task is not None:
                self.task = None

    def _solve_code(self, raw_code: str) -> T_Executor:
        assert self.locked, "`Context._solve_code` must be called with lock"

        # 预处理代码
        lines: list[str] = [
            f"global {', '.join(self.ctx.keys())}",
            *raw_code.split("\n"),
        ]
        solved = EXECUTOR_FUNCTION.replace("{CODE}", f"\n{EXECUTOR_INDENT}".join(lines))
        code = compile(solved, f"<executor_{self.uin}>", "exec")

        # 包装为异步函数
        exec(code, self.ctx, self.ctx)
        return self.ctx.pop("__executor__")

    @classmethod
    async def execute(cls, bot: Bot, session: Session, code: str) -> None:
        uin = cls._session2uin(session)
        self = cls.get_context(session)
        API = get_api_class(bot)

        # 执行代码时加锁，避免出现多段代码分别读写变量
        async with self._lock():
            API(bot, session).export_to(self.ctx)
            executor = self._solve_code(code)
            logger.debug(f"为用户 <y>{uin}</y> 创建 executor: {executor}")
            self.task = get_event_loop().create_task(executor())
            result, self.task = await self.task, None

            if buf := Buffer.get(uin).read().rstrip("\n"):
                await UniMessage.text(buf).send()
            if result is not None:
                await UniMessage.text(repr(result)).send()

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
