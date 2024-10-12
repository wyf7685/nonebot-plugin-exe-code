import contextlib

from nonebot.adapters import Event
from typing_extensions import override

from ..api import API as BaseAPI
from ..api import register_api
from ..help_doc import descript
from ..utils import debug_log, strict

with contextlib.suppress(ImportError):
    from nonebot.adapters.satori import Adapter, Bot, MessageEvent

    @register_api(Adapter)
    class API(BaseAPI[Bot, MessageEvent]):
        __slots__ = ()

        @classmethod
        @override
        def _validate(cls, bot: Bot, event: Event) -> bool:
            return isinstance(bot, Bot) and isinstance(event, MessageEvent)

        @descript(
            description="设置群禁言",
            parameters=dict(
                duration="禁言时间, 单位秒, 填0为解除禁言",
                qid="被禁言者ID",
                gid="所在群组ID, 默认为当前群聊, 私聊时必填",
            ),
        )
        @debug_log
        @strict
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
            await self.bot.guild_member_mute(
                guild_id=str(gid),
                user_id=str(qid or self.qid),
                duration=float(duration) * 1000,
            )

        @descript(
            description="[nekobox] 群聊消息回应",
            parameters=dict(
                emoji_id="回应的表情ID",
                message_id="需要回应的消息ID，可通过getmid获取",
                channel_id="指定群组ID，默认为当前群组",
            ),
        )
        @debug_log
        @strict
        async def set_reaction(
            self,
            emoji_id: int,
            message_id: str | int,
            channel_id: str | int | None = None,
        ) -> None:
            if channel_id is None:
                channel_id = self.gid
            if (channel_id := str(channel_id)).startswith("private:"):
                raise ValueError("未指定群组ID")

            await self.bot.reaction_create(
                channel_id=channel_id,
                message_id=str(message_id),
                emoji=f"face:{emoji_id}",
            )
