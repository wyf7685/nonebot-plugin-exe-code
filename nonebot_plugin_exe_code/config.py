from nonebot import get_plugin_config
from pydantic import BaseModel, Field


class ExeCodeConfig(BaseModel):
    user: set[str] = Field(default_factory=set)
    group: set[str] = Field(default_factory=set)


class Config(BaseModel):
    exe_code: ExeCodeConfig = Field(default_factory=ExeCodeConfig)


config = get_plugin_config(Config).exe_code
