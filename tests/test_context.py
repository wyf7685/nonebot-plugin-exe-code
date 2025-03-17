# ruff: noqa: S101

import asyncio
from typing import override

import pytest
from nonebot.adapters.onebot.v11 import Message
from nonebug import App

from .fake.common import ensure_context
from .fake.onebot11 import fake_v11_bot, fake_v11_event_session


@pytest.mark.asyncio
async def test_lock(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, _ = fake_v11_event_session(bot)

        async def _test(delay: float, code: str) -> None:
            await asyncio.sleep(delay)
            await Context.execute(bot, event, code)

        ctx.should_call_send(event, Message("1"))
        ctx.should_call_send(event, Message("2"))

        with ensure_context(bot, event):
            await asyncio.gather(
                _test(0, "print(1); await sleep(0.1)"),
                _test(0.01, "print(2)"),
            )


@pytest.mark.asyncio
async def test_cancel(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, session = fake_v11_event_session(bot)
        result = False

        async def _test1() -> None:
            with pytest.raises(asyncio.CancelledError):
                await Context.execute(bot, event, "await sleep(1); print(1)")

        async def _test2() -> None:
            nonlocal result
            await asyncio.sleep(0.01)
            result = Context.get_context(session).cancel()

        with ensure_context(bot, event):
            await asyncio.gather(_test1(), _test2())
        assert result


@pytest.mark.asyncio
async def test_context_variable(app: App) -> None:
    from nonebot_plugin_alconna.uniseg import Image, UniMessage

    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        _, session = fake_v11_event_session(bot)
        context = Context.get_context(session)

    key, val = "aaa", 111
    context.set_value(key, val)
    assert context.ctx.get(key) == val
    context.set_value(key, None)
    assert key not in context.ctx

    key, val = "gurl", "http://localhost/image.png"
    unimsg = UniMessage.image(url=val)
    context.set_gurl(unimsg)
    assert context.ctx.pop(key) == val
    context.set_gurl(unimsg[Image, 0])
    assert context.ctx.pop(key) == val
    context.set_gurl(UniMessage())
    assert key not in context.ctx

    key, val = "abc", 123
    context[key] = val
    assert context[key] == val
    del context[key]
    assert key not in context.ctx


@pytest.mark.asyncio
async def test_session_fetch(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.exception import (
        BotEventMismatch,
        SessionNotInitialized,
    )

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, session = fake_v11_event_session(bot)
        wrong_event, _ = fake_v11_event_session(bot)

        with (
            ensure_context(bot, wrong_event),
            pytest.raises(BotEventMismatch),
        ):
            Context.get_context(event)

        with ensure_context(bot, event):
            with pytest.raises(SessionNotInitialized):
                Context.get_context(event)
            with pytest.raises(SessionNotInitialized):
                Context.get_context(event.get_user_id())

            Context.get_context(session)
            Context.get_context(event)
            Context.get_context(event.get_user_id())


@pytest.mark.asyncio
async def test_async_generator_executor(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.interface.utils import ReachLimit

    ReachLimit.limit = 3

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, session = fake_v11_event_session(bot)

        ctx.should_call_send(event, Message("1"))
        ctx.should_call_send(event, Message("2"))
        ctx.should_call_send(event, Message("0"))
        with ensure_context(bot, event), pytest.raises(ReachLimit):
            await Context.get_context(session).execute(
                bot, event, "yield 1\nyield 2\nyield from range(3)"
            )


@pytest.mark.asyncio
async def test_delete_builtins(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, session = fake_v11_event_session(bot)

        with ensure_context(bot, event):
            context = Context.get_context(session)
            assert context.ctx.pop("__builtins__", None) is not None
            await context.execute(bot, event, "api, UniMessage")
            assert "__builtins__" in context.ctx


@pytest.mark.asyncio
async def test_context_namespace(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event, session = fake_v11_event_session(bot)

        with ensure_context(bot, event):
            context = Context.get_context(session)
            await context.execute(bot, event, "a = 1")
            assert context.ctx["a"] == 1
            await context.execute(bot, event, "a = 2")
            assert context.ctx["a"] == 2
            await context.execute(bot, event, "del a")
            assert "a" not in context.ctx


code_test_ast_node_transformer_convert = """\
yield y
yield from z
return x
"""
code_test_ast_node_transformer_func_def = """\
def _() -> X:
    return x
async def _():
    yield y
    yield from z
"""


def test_ast_node_transformer() -> None:
    import ast

    from nonebot_plugin_exe_code.context import _NodeTransformer as Transformer

    class Visitor1(ast.NodeVisitor):
        await_visited = False

        @override
        def visit_Return(self, node: ast.Return) -> None:
            pytest.fail("Return should be transformed")

        @override
        def visit_Yield(self, node: ast.Yield) -> None:
            pytest.fail("Yield should be transformed")

        @override
        def visit_YieldFrom(self, node: ast.YieldFrom) -> None:
            pytest.fail("YieldFrom should be transformed")

        @override
        def visit_Await(self, node: ast.Await) -> ast.Await:
            expected = {"x": "finish", "y": "feedback", "z": "feedback_from"}
            match node.value:
                case ast.Call(
                    func=ast.Attribute(value=ast.Name(id="__api__"), attr=api_attr),
                    args=[ast.Name(id=key)],
                ):
                    assert api_attr == expected[key]
                    Visitor1.await_visited = True
                    return node
            pytest.fail("Await not added correctly")

    tree = ast.parse(code_test_ast_node_transformer_convert)
    transformed = Transformer().visit(tree)
    Visitor1().visit(transformed)
    assert Visitor1.await_visited, "Await not added"

    class Visitor2(ast.NodeVisitor):
        @override
        def visit_Return(self, node: ast.Return) -> None:
            match node.value:
                case ast.Name(id="x"):
                    return
            pytest.fail("Return should not be transformed")

        @override
        def visit_Yield(self, node: ast.Yield) -> None:
            match node.value:
                case ast.Name(id="y"):
                    return
            pytest.fail("Yield should not be transformed")

        @override
        def visit_YieldFrom(self, node: ast.YieldFrom) -> None:
            match node.value:
                case ast.Name(id="z"):
                    return
            pytest.fail("YieldFrom should not be transformed")

    tree = ast.parse(code_test_ast_node_transformer_func_def)
    transformed = Transformer().visit(tree)
    Visitor2().visit(transformed)
