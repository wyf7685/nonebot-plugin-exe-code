from io import BytesIO
from typing import NoReturn

import PIL.Image
from nonebot import on_message
from nonebot.adapters import Bot, Event
from nonebot_plugin_alconna.uniseg import UniMessage, image_fetch

from .depends import AllowExeCode, CodeContext, EventImage, startswith

matcher = on_message(startswith("getimg"), permission=AllowExeCode)


@matcher.handle()
async def handle_getimg(
    bot: Bot,
    event: Event,
    ctx: CodeContext,
    image: EventImage,
) -> NoReturn:
    varname = (
        event.get_message().extract_plain_text().strip().removeprefix("getimg").strip()
    )
    if (varname := varname or "img") and not varname.isidentifier():
        await UniMessage(f"{varname} 不是一个合法的 Python 标识符").finish()

    try:
        img_bytes = await image_fetch(event, bot, {}, image)
    except Exception as err:
        await UniMessage(f"保存图片时出错: {err}").finish()

    if not isinstance(img_bytes, bytes):
        await UniMessage(f"获取图片数据类型错误: {type(img_bytes)!r}").finish()

    async with ctx.lock():
        ctx.set_gurl(image)
        ctx.set_value(varname, PIL.Image.open(BytesIO(img_bytes)))
    await UniMessage(f"图片已保存至变量 {varname}").finish()
