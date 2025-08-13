from typing import Annotated, NoReturn

from nonebot.adapters import Event
from nonebot.params import Depends
from nonebot.permission import SUPERUSER
from nonebot_plugin_alconna import Alconna, Args, on_alconna
from nonebot_plugin_alconna.uniseg import At, UniMessage

from ..context import Context

matcher = on_alconna(Alconna("terminate", Args["target?", At]), permission=SUPERUSER)


def _target(event: Event, target: At | None = None) -> str:
    return target.target if target is not None else event.get_user_id()


async def _context(target: Annotated[str, Depends(_target)]) -> Context:
    try:
        return Context.get_context(target)
    except Exception as err:
        await matcher.finish(f"获取 Context 失败: {err}")


@matcher.handle()
async def handle_terminate(
    target: Annotated[str, Depends(_target)],
    context: Annotated[Context, Depends(_context)],
) -> NoReturn:
    if context.cancel():
        await UniMessage("中止").at(target).text("的执行任务").send()
    await matcher.finish()
