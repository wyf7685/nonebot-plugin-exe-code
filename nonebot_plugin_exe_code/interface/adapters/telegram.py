import contextlib
from typing import override

from nonebot.adapters import Event
from nonebot.exception import ActionFailed

from ...exception import APICallFailed as BaseAPICallFailed
from ...exception import ParamMismatch
from ..api import API as BaseAPI
from ..decorators import debug_log, strict
from ..help_doc import descript

with contextlib.suppress(ImportError):
    from nonebot.adapters.telegram import Adapter, Bot
    from nonebot.adapters.telegram.event import MessageEvent
    from nonebot.adapters.telegram.exception import ActionFailed
    from nonebot.adapters.telegram.model import ReactionTypeEmoji

    class APICallFailed(BaseAPICallFailed, ActionFailed): ...

    class API(BaseAPI[Bot, MessageEvent], adapter=Adapter):
        __slots__ = ()

        @classmethod
        @override
        def _validate(cls, bot: Bot, event: Event) -> bool:
            return isinstance(bot, Bot) and isinstance(event, MessageEvent)

        @descript(
            description="消息回应",
            parameters=dict(
                emoji="回应的 emoji",
                message_id="需要回应的消息ID，默认为当前回复消息/当前消息",
                chat_id="指定对话ID，默认为当前对话",
            ),
        )
        @debug_log
        @strict
        async def set_reaction(
            self,
            emoji: str,
            message_id: str | int | None = None,
            chat_id: str | int | None = None,
        ) -> None:
            if message_id is None:
                message_id = self.event.message_id
                if self.event.reply_to_message:
                    message_id = self.event.reply_to_message.message_id
            elif isinstance(message_id, str) and not message_id.isdigit():
                raise ParamMismatch("message_id 应为数字")
            message_id = int(message_id)

            if chat_id is None:
                chat_id = self.event.chat.id
            elif isinstance(chat_id, str) and not chat_id.isdigit():
                raise ParamMismatch("chat_id 应为数字")
            chat_id = int(chat_id)

            try:
                await self.bot.set_message_reaction(
                    chat_id=chat_id,
                    message_id=message_id,
                    reaction=[ReactionTypeEmoji(type="emoji", emoji=emoji)],
                )
            except ActionFailed as e:
                raise APICallFailed(f"调用 API set_message_reaction 失败: {e}") from e
