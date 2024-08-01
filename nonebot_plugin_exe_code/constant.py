from typing import Any, Callable, Coroutine, Optional, Union

from nonebot.adapters import Message, MessageSegment
from nonebot_plugin_alconna.uniseg import Segment, UniMessage

# description
DESCRIPTION_FORMAT = "{decl}\n* 描述: {desc}\n* 参数:\n{params}\n* 返回值:\n  {res}\n"
DESCRIPTION_RESULT_TYPE = "Result类对象，可通过属性名获取接口响应"
DESCRIPTION_RECEIPT_TYPE = "UniMessage发送后返回的Receipt对象，用于操作对应消息"

# interface
INTERFACE_INST_NAME = "__inst_name__"
INTERFACE_EXPORT_METHOD = "__export_method__"
INTERFACE_METHOD_DESCRIPTION = "__method_description__"


T_Context = dict[str, Any]
T_Executor = Callable[[], Coroutine[None, None, Any]]
T_API_Result = Optional[Union[dict[str, Any], list[Any]]]
T_Message = Union[str, Message, MessageSegment, UniMessage, Segment]
T_ForwardMsg = list[T_Message]
T_ConstVar = Union[str, bool, int, float, dict[str, "T_ConstVar"], list["T_ConstVar"]]
T_OptConstVar = Optional[T_ConstVar]
