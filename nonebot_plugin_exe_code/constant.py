from nonebot_plugin_localstore import get_data_dir

DATA_DIR = get_data_dir("nonebot_plugin_exe_code")

# description
DESCRIPTION_FORMAT = "{decl}\n* 描述: {desc}\n* 参数:\n{params}\n* 返回值:\n  {res}\n"
DESCRIPTION_RESULT_TYPE = "Result类对象，可通过属性名获取接口响应"
DESCRIPTION_RECEIPT_TYPE = "UniMessage发送后返回的Receipt对象，用于操作对应消息"

# interface
INTERFACE_INST_NAME = "__inst_name__"
INTERFACE_EXPORT_METHOD = "__export_method__"
INTERFACE_METHOD_DESCRIPTION = "__method_description__"
