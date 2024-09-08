import contextlib
from typing import cast

from ..api import API as BaseAPI
from ..api import register_api
from ..help_doc import descript
from ..utils import debug_log

with contextlib.suppress(ImportError):
    from nonebot.adapters.satori import Adapter, Bot

    @register_api(Adapter)
    class API(BaseAPI):
        @descript(
            description="设置群禁言",
            parameters=dict(
                duration="禁言时间, 单位秒, 填0为解除禁言",
                qid="被禁言者ID",
                gid="所在群组ID, 默认为当前群聊, 私聊时必填",
            ),
        )
        @debug_log
        async def set_mute(
            self,
            duration: float,
            qid: str | int | None = None,
            gid: str | int | None = None,
        ) -> None:
            if gid is None:
                gid = self.gid
            if (gid := str(gid)).startswith("private:"):
                raise ValueError("未指定群组ID")
            await cast(Bot, self.bot).guild_member_mute(
                guild_id=str(gid),
                user_id=str(qid or self.qid),
                duration=float(duration) * 1000,
            )
