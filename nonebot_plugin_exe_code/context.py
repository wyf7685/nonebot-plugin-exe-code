import ast
import contextlib
import functools
import inspect
import linecache
import sys
import time
import traceback
from collections.abc import Awaitable, Callable, Generator
from typing import Any, ClassVar, Self, cast

import anyio
import anyio.abc
import nonebot
from nonebot import get_driver
from nonebot.adapters import Bot, Event, Message
from nonebot.internal.matcher import current_bot, current_event
from nonebot.utils import escape_tag
from nonebot_plugin_alconna.uniseg import Image, UniMessage
from nonebot_plugin_session import Session, SessionIdType, extract_session

from .exception import BotEventMismatch, SessionNotInitialized
from .interface import API, Buffer, get_api_class, get_default_context
from .typings import T_Context

logger = nonebot.logger.opt(colors=True)

EXECUTOR_FUNCTION = """\
async def __executor__(__context__, /):
    with __context__:
        del __context__
"""
ASYNCGEN_WRAPPER = """\
async def wrapper():
    try:
        async for value in gen():
            await api.feedback(repr(value))
    except BaseException as err:
        import traceback
        ctx["__exception__"] = (err, traceback.format_exc())
"""
type T_Executor = Callable[[], Awaitable[object]]
type T_ExecutorCtx = Callable[[], contextlib.AbstractContextManager[None]]


async def _cleanup(
    delay: float,
    callbacks: list[Callable[[], object]],
) -> None:  # pragma: no cover
    await anyio.sleep(delay)

    for callback in callbacks:
        with contextlib.suppress(Exception):
            callback()


@contextlib.contextmanager
def fake_cache(filename: str, code: str) -> Generator[None]:
    cbs: list[Callable[[], object]] = []

    # https://docs.python.org/3/library/linecache.html
    # linecache.cache is undocumented and may change in the future
    with contextlib.suppress(Exception):
        cache = (len(code), None, [line + "\n" for line in code.splitlines()], filename)
        linecache.cache[filename] = cache
        cbs.append(lambda: linecache.cache.pop(filename, None))

    # set modulesbyfile[name] to this module temporarily
    # allow inspect.getmodule to work on executor frame
    fake_abs_filename = inspect.getabsfile(object, filename)
    inspect.modulesbyfile[fake_abs_filename] = __name__
    cbs.append(lambda: inspect.modulesbyfile.pop(fake_abs_filename, None))

    try:
        yield
    finally:
        get_driver().task_group.start_soon(_cleanup, 300, cbs)


@contextlib.contextmanager
def setup_ctx(ctx: T_Context) -> Generator[None]:
    localns = sys._getframe(2).f_locals  # noqa: SLF001
    old_names = set(filter(lambda x: not x.startswith("__"), ctx))
    for name in old_names:
        localns[name] = ctx[name]
    localns["exc"], localns["tb"] = ctx.pop("__exception__", (None, None))
    localns["__exception__"] = (None, None)

    try:
        yield
    except BaseException as e:
        ctx["__exception__"] = (e, traceback.format_exc())
    finally:
        new_names = set(filter(lambda x: not x.startswith("__"), localns))
        for name in old_names - new_names:
            del ctx[name]
        for name in (old_names & new_names) | (new_names - old_names):
            ctx[name] = localns[name]


class Context:
    __ua2session: ClassVar[dict[tuple[str, str], Session]] = {}
    __contexts: ClassVar[dict[str, Self]] = {}

    uin: str
    ctx: T_Context
    lock: anyio.Lock
    cancel_scope: anyio.CancelScope | None = None

    def __init__(self, uin: str) -> None:
        self.uin = uin
        self.ctx = get_default_context()
        self.lock = anyio.Lock()

    @classmethod
    def _session2uin(cls, session: Session | Event | str) -> str:
        if isinstance(session, Event):
            if current_event.get() is not session:
                raise BotEventMismatch
            key = (session.get_user_id(), current_bot.get().type)
            if key not in cls.__ua2session:
                raise SessionNotInitialized(key=key)
            session = cls.__ua2session[key]
        elif isinstance(session, str):
            key = (session, current_bot.get().type)
            if key not in cls.__ua2session:
                raise SessionNotInitialized(key=key)
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

    def _solve_code(self, raw_code: str, api: API) -> tuple[T_Executor, T_ExecutorCtx]:
        assert self.lock.locked(), "`Context._solve_code` called without lock"

        # 可能抛出 SyntaxError, 由 matcher 处理
        stmts = ast.parse(raw_code, mode="exec").body

        # 将解析后的代码插入到 try 语句块中
        parsed = ast.parse(EXECUTOR_FUNCTION, mode="exec")
        func_def = next(x for x in parsed.body if isinstance(x, ast.AsyncFunctionDef))
        next(x for x in func_def.body if isinstance(x, ast.With)).body.extend(stmts)
        solved = ast.unparse(parsed)

        filename = f"<executor_{self.uin}_{int(time.time())}>"
        code = compile(solved, filename, "exec")

        # 包装为异步函数
        exec(code, self.ctx, self.ctx)  # noqa: S102
        executor: T_Executor = functools.partial(
            self.ctx.pop(func_def.name),
            setup_ctx(self.ctx),
        )

        if inspect.isasyncgenfunction(executor):
            ns = {"ctx": self.ctx, "api": api, "gen": executor}
            exec(ASYNCGEN_WRAPPER, ns, ns)  # noqa: S102
            executor = ns.pop("wrapper")

        return executor, functools.partial(fake_cache, filename, solved)

    @classmethod
    async def execute(cls, bot: Bot, event: Event, code: str) -> None:
        session = extract_session(bot, event)
        uin = cls._session2uin(session)
        colored_uin = f"<y>{escape_tag(uin)}</y>"
        self = cls.get_context(session)
        api = get_api_class(bot)(bot, event, session, self.ctx)

        # 执行代码时加异步锁，避免出现多段代码分别读写变量
        # api 导出接口到 ctx
        async with self.lock, api:
            executor, ctx = self._solve_code(code, api)
            escaped = escape_tag(repr(executor))
            logger.debug(f"为用户 {colored_uin} 创建 executor: {escaped}")

            result = None
            with anyio.CancelScope() as self.cancel_scope, ctx():
                result = await executor()
            self.cancel_scope = None

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
        if self.cancel_scope is None:
            return False
        self.cancel_scope.cancel()
        return True

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
