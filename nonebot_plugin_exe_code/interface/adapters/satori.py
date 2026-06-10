import contextlib
from typing import override

from nonebot.adapters import Event

from ...exception import ParamMissing
from ..api import API as BaseAPI
from ..decorators import debug_log, strict
from ..help_doc import descript

with contextlib.suppress(ImportError):
    from nonebot.adapters.satori import Adapter, Bot, MessageEvent

    class API(BaseAPI[Bot, MessageEvent], adapter=Adapter):
        __slots__ = ()

        @classmethod
        @override
        def _validate(cls, bot: Bot, event: Event) -> bool:
            return isinstance(bot, Bot) and isinstance(event, MessageEvent)

        @descript(
            description="获取当前平台类型",
            parameters=None,
            result="当前平台类型",
        )
        @debug_log
        @override
        async def get_platform(self: BaseAPI[Bot, MessageEvent]) -> str:
            login = await self.bot.login_get()
            platform = login.platform or "Unkown"
            return f"[{self.bot.type}] {platform}"

        @descript(
            description="设置群禁言",
            parameters=dict(
                duration="禁言时间, 单位秒, 填0为解除禁言",
                uid="被禁言者ID",
                gid="所在群组ID, 默认为当前群聊, 私聊时必填",
            ),
        )
        @debug_log
        @strict
        async def set_mute(
            self,
            duration: int | float,  # noqa: PYI041
            uid: str | int | None = None,
            gid: str | int | None = None,
        ) -> None:
            if gid is None:
                gid = self.gid
            if (gid := str(gid)).startswith("private:"):
                raise ParamMissing("未指定群组ID")
            await self.bot.guild_member_mute(
                guild_id=str(gid),
                user_id=str(uid or self.uid),
                duration=float(duration) * 1000,
            )
