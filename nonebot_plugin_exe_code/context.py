import ast
import contextlib
import functools
import inspect
import linecache
import time
import traceback
import types
from collections.abc import Awaitable, Callable, Generator
from typing import Any, ClassVar, Self, assert_never, cast, override

import anyio
import nonebot
from nonebot import get_driver
from nonebot.adapters import Bot, Event, Message
from nonebot.internal.matcher import current_bot, current_event
from nonebot.utils import escape_tag, run_sync
from nonebot_plugin_alconna.uniseg import Image, UniMessage
from nonebot_plugin_uninfo import get_session
from nonebot_plugin_user.models import UserSession
from nonebot_plugin_user.params import get_user_session

from .exception import (
    BotEventMismatch,
    ExecutorFinishedException,
    SessionNotInitialized,
)
from .interface import Buffer, create_api, get_default_context
from .typings import T_Context

logger = nonebot.logger.opt(colors=True)

type T_Executor = Callable[[], Awaitable[None]]
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
        # cleanup cache later (300s)
        get_driver().task_group.start_soon(_cleanup, 300, cbs)


class _NodeTransformer(ast.NodeTransformer):
    _handler = ast.ExceptHandler(
        ast.Name("InternalException", ctx=ast.Load()),
        body=[ast.Raise()],
    )
    enabled: bool = True

    @classmethod
    def transform[T: ast.AST](cls, node: T) -> T:
        """Transform AST node."""
        return cls().visit(node)

    @staticmethod
    @functools.lru_cache(maxsize=16)
    def _api(name: str) -> ast.expr:
        return ast.Attribute(ast.Name("__api__", ctx=ast.Load()), name, ctx=ast.Load())

    @contextlib.contextmanager
    def disable_transform(self) -> Generator[None, None, None]:
        self.enabled, enabled = False, self.enabled
        try:
            yield
        finally:
            self.enabled = enabled

    def call_api(self, name: str, arg: ast.expr | None) -> ast.expr:
        args = [self.visit(arg)] if arg else []
        return ast.Await(ast.Call(self._api(name), args, []))

    def _visit_function[T: (ast.FunctionDef, ast.AsyncFunctionDef)](self, node: T) -> T:
        with self.disable_transform():
            for member in node.decorator_list, node.body:
                member[:] = map(self.visit, member.copy())
            node.args = self.visit(node.args)
            if node.returns is not None:
                node.returns = self.visit(node.returns)
            return node

    @override
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        return self._visit_function(node)

    @override
    def visit_AsyncFunctionDef(
        self, node: ast.AsyncFunctionDef
    ) -> ast.AsyncFunctionDef:
        return self._visit_function(node)

    @override
    def visit_Return(self, node: ast.Return) -> ast.stmt:
        return ast.Expr(self.call_api("finish", node.value)) if self.enabled else node

    @override
    def visit_Yield(self, node: ast.Yield) -> ast.expr:
        return self.call_api("feedback", node.value) if self.enabled else node

    @override
    def visit_YieldFrom(self, node: ast.YieldFrom) -> ast.expr:
        return self.call_api("feedback_from", node.value) if self.enabled else node

    @override
    def visit_Try(self, node: ast.Try) -> ast.Try:
        if not self.enabled:
            return node

        for member in (node.body, node.handlers, node.orelse, node.finalbody):
            member[:] = map(self.visit, member.copy())
        node.handlers.insert(0, self._handler)
        return node


def solve_code(
    source: str,
    filename: str,
    ctx: dict[str, object],
) -> tuple[T_Executor, T_ExecutorCtx]:
    # 可能抛出 SyntaxError, 由 matcher 处理
    parsed = ast.parse(source)

    solved = ast.fix_missing_locations(_NodeTransformer.transform(parsed))
    code: types.CodeType = compile(
        source=solved,
        filename=filename,
        mode="exec",
        flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT,
    )

    is_coro = bool(code.co_flags & inspect.CO_COROUTINE)
    exec(f"{('async ' if is_coro else '')}def __executor__(): ...", ctx, ctx)  # noqa: S102
    executor = cast(Callable[..., Any], ctx.pop("__executor__"))
    executor.__code__ = code
    if not is_coro:
        executor = run_sync(executor)

    ctx["__name__"] = filename
    return executor, functools.partial(fake_cache, filename, ast.unparse(solved))


class Context:
    __ua2uin: ClassVar[dict[tuple[str, str], int]] = {}
    __contexts: ClassVar[dict[int, Self]] = {}

    uin: int
    ctx: T_Context
    lock: anyio.Lock
    cancel_scope: anyio.CancelScope | None = None

    def __init__(self, uin: int) -> None:
        self.uin = uin
        self.ctx = get_default_context()
        self.lock = anyio.Lock()

    @classmethod
    def _session2uin(cls, session: UserSession | Event | str | int) -> int:
        match session:
            case UserSession():
                uin = session.user_id
                key = (session.platform_user.id, session.adapter)
                cls.__ua2uin[key] = uin
            case Event():
                if current_event.get() is not session:
                    raise BotEventMismatch
                key = (session.get_user_id(), current_bot.get().type)
                if key not in cls.__ua2uin:
                    raise SessionNotInitialized(key=key)
                uin = cls.__ua2uin[key]
            case str():
                key = (session, current_bot.get().type)
                if key not in cls.__ua2uin:
                    raise SessionNotInitialized(key=key)
                uin = cls.__ua2uin[key]
            case int():
                uin = session
            case _:  # pragma: no cover
                assert_never(session)

        return uin

    @classmethod
    def get_context(cls, session: UserSession | Event | str | int) -> Self:
        uin = cls._session2uin(session)
        if uin not in cls.__contexts:
            logger.debug(f"为用户 <y>{uin}</y> 创建 Context")
            cls.__contexts[uin] = cls(uin)

        return cls.__contexts[uin]

    @property
    def colored_uin(self) -> str:
        return f"<y>{self.uin}</y>"

    def _get_filename(self) -> str:
        return f"<executor_{self.uin}_{int(time.time())}>"

    async def _check_buffer(self) -> None:
        if buf := Buffer.get(self.uin).read().rstrip("\n"):
            logger.debug(f"用户 {self.colored_uin} 清空缓冲:")
            logger.opt(raw=True).debug(buf)
            await UniMessage.text(buf).send()

    async def _inner_execute(
        self, executor: T_Executor
    ) -> tuple[object, BaseException | None]:
        result = err = None

        with anyio.CancelScope() as self.cancel_scope:
            try:
                await executor()
            except ExecutorFinishedException as finished:
                result = finished.result
            except BaseException as exc:
                self.ctx["exc"] = err = exc
                self.ctx["tb"] = traceback.format_exc()
            finally:
                self.cancel_scope = None

        return result, err

    @classmethod
    async def execute(cls, bot: Bot, event: Event, code: str) -> None:
        session = await get_user_session(await get_session(bot, event))
        if session is None:
            raise NotImplementedError

        self = cls.get_context(session)

        # 执行代码时加异步锁，避免出现多段代码分别读写变量
        # api 导出接口到 ctx
        async with self.lock, await create_api(bot, event, self.ctx):
            executor, ctx = solve_code(code, self._get_filename(), self.ctx)
            logger.debug(
                f"为用户 {self.colored_uin} 创建 executor: {escape_tag(repr(executor))}"
            )

            with ctx():
                result, err = await self._inner_execute(executor)

            await self._check_buffer()

            if result is not None:
                result_repr = repr(result)
                logger.debug(
                    f"用户 {self.colored_uin} 输出返回值: {escape_tag(result_repr)}"
                )
                await UniMessage.text(result_repr).send()

            # 处理异常
            if err is not None:
                raise err

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

    def set_gurl(self, msg: UniMessage | Image) -> None:
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
