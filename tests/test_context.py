from typing import override

import anyio
import pytest
from nonebot.adapters.onebot.v11 import Message
from nonebug import App

from .fake.common import ensure_context, fake_session
from .fake.onebot11 import fake_v11_bot, fake_v11_event


@pytest.mark.anyio
async def test_lock(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event = fake_v11_event()

        async def _test(delay: float, code: str) -> None:
            await anyio.sleep(delay)
            await Context.execute(bot, event, code)

        ctx.should_call_send(event, Message("1"))
        ctx.should_call_send(event, Message("2"))
        ctx.should_call_send(event, Message("3"))

        async with ensure_context(bot, event), anyio.create_task_group() as tg:
            tg.start_soon(_test, 0, "print(1); await sleep(0.1); return 2")
            tg.start_soon(_test, 0.01, "print(3)")


@pytest.mark.anyio
async def test_cancel(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event = fake_v11_event()
        session = await fake_session(bot, event)
        result = False

        async def _test1() -> None:
            with pytest.raises(anyio.get_cancelled_exc_class()):
                await Context.execute(bot, event, "await sleep(1); return 1")

        async def _test2() -> None:
            nonlocal result
            await anyio.sleep(0.1)
            result = Context.get_context(session).cancel()

        async with ensure_context(bot, event), anyio.create_task_group() as tg:
            tg.start_soon(_test1)
            tg.start_soon(_test2)

        assert result


@pytest.mark.anyio
async def test_context_variable(app: App) -> None:
    from nonebot_plugin_alconna.uniseg import Image, UniMessage

    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        session = await fake_session(fake_v11_bot(ctx), fake_v11_event())
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


@pytest.mark.anyio
async def test_session_fetch(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.exception import (
        BotEventMismatch,
        SessionNotInitialized,
    )

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event = fake_v11_event()
        session = await fake_session(bot, event)
        wrong_event = fake_v11_event()

        async with ensure_context(bot, wrong_event):
            with pytest.raises(BotEventMismatch):
                Context.get_context(event)

        async with ensure_context(bot, event):
            with pytest.raises(SessionNotInitialized):
                Context.get_context(event)
            with pytest.raises(SessionNotInitialized):
                Context.get_context(event.get_user_id())

            context = Context.get_context(session)
            assert Context.get_context(event) is context
            assert Context.get_context(event.get_user_id()) is context
            assert Context.get_context(context.uin) is context


@pytest.mark.anyio
async def test_async_generator_executor(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context
    from nonebot_plugin_exe_code.interface.utils import ReachLimit

    ReachLimit.limit = 3

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event = fake_v11_event()
        session = await fake_session(bot, event)

        ctx.should_call_send(event, Message("1"))
        ctx.should_call_send(event, Message("2"))
        ctx.should_call_send(event, Message("0"))
        async with ensure_context(bot, event):
            with pytest.raises(ReachLimit):
                await Context.get_context(session).execute(
                    bot, event, "yield 1\nyield 2\nyield from range(3)"
                )


@pytest.mark.anyio
async def test_delete_builtins(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event = fake_v11_event()
        session = await fake_session(bot, event)

        async with ensure_context(bot, event):
            context = Context.get_context(session)
            assert context.ctx.pop("__builtins__", None) is not None
            await context.execute(bot, event, "api, UniMessage")
            assert "__builtins__" in context.ctx


@pytest.mark.anyio
async def test_context_namespace(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event = fake_v11_event()
        session = await fake_session(bot, event)

        async with ensure_context(bot, event):
            context = Context.get_context(session)
            await context.execute(bot, event, "a = 1")
            assert context.ctx["a"] == 1
            await context.execute(bot, event, "a = 2")
            assert context.ctx["a"] == 2
            await context.execute(bot, event, "del a")
            assert "a" not in context.ctx


@pytest.mark.anyio
async def test_create_class(app: App) -> None:
    from nonebot_plugin_exe_code.context import Context

    async with app.test_api() as ctx:
        bot = fake_v11_bot(ctx)
        event = fake_v11_event()
        session = await fake_session(bot, event)

        async with ensure_context(bot, event):
            context = Context.get_context(session)
            await context.execute(bot, event, "class A: ...")
            cls = context.ctx["A"]
            assert isinstance(cls, type)
            assert cls.__name__ == "A"


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
code_test_ast_node_transformer_try = """\
try:
    yield y
finally:
    yield from z
"""
code_test_ast_node_transformer_try_func_def = """\
def _() -> X:
    try:
        yield y
    finally:
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

    class Visitor3(ast.NodeVisitor):
        @override
        def visit_Yield(self, node: ast.Yield) -> None:
            pytest.fail("Yield should be transformed")

        @override
        def visit_YieldFrom(self, node: ast.YieldFrom) -> None:
            pytest.fail("YieldFrom should be transformed")

    tree = ast.parse(code_test_ast_node_transformer_try)
    transformed = Transformer().visit(tree)
    Visitor3().visit(transformed)

    class Visitor4(ast.NodeVisitor):
        yield_visited = False
        yield_from_visited = False

        @override
        def visit_Yield(self, node: ast.Yield) -> None:
            match node.value:
                case ast.Name(id="y"):
                    Visitor4.yield_visited = True
                    return
            pytest.fail("Yield should not be transformed")

        @override
        def visit_YieldFrom(self, node: ast.YieldFrom) -> None:
            match node.value:
                case ast.Name(id="z"):
                    Visitor4.yield_from_visited = True
                    return
            pytest.fail("YieldFrom should not be transformed")

    tree = ast.parse(code_test_ast_node_transformer_try_func_def)
    transformed = Transformer().visit(tree)
    Visitor4().visit(transformed)
    assert Visitor4.yield_visited, "Yield should not be transformed"
    assert Visitor4.yield_from_visited, "YieldFrom should not be transformed"
