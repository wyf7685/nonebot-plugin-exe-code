from typing import Annotated

from nonebot.adapters import Event
from nonebot.params import Depends
from nonebot.permission import SUPERUSER
from nonebot_plugin_alconna import Alconna, Args, Match, on_alconna
from nonebot_plugin_alconna.uniseg import At, UniMessage

from ..context import Context

matcher = on_alconna(Alconna("terminate", Args["target?", At]), permission=SUPERUSER)


def _target(event: Event, target: Match[At]) -> str:
    return target.result.target if target.available else event.get_user_id()


@matcher.handle()
async def handle_terminate(target: Annotated[str, Depends(_target)]):
    if Context.get_context(target).cancel():
        await UniMessage("中止").at(target).text("的执行任务").send()
