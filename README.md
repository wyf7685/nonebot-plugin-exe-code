<div align="center">
  <a href="https://v2.nonebot.dev/store"><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/nbp_logo.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
  <br>
  <p><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/NoneBotPlugin.svg" width="240" alt="NoneBotPluginText"></p>
</div>

<div align="center">

# nonebot-plugin-exe-code

_✨ 在聊天中执行带有上下文的 Python 代码 ✨_

[![license](https://img.shields.io/github/license/wyf7685/nonebot-plugin-exe-code.svg)](./LICENSE)
[![pypi](https://img.shields.io/pypi/v/nonebot-plugin-exe-code.svg)](https://pypi.python.org/pypi/nonebot-plugin-exe-code)
![python](https://img.shields.io/badge/python-3.12+-blue.svg)

[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1)](https://pycqa.github.io/isort/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

</div>

## 📖 介绍

本插件旨在允许开发者在聊天中执行带有上下文的 Python 代码，从而对 NoneBot 框架进行运行时侵入式修改。由于这种设计，插件具有极高的灵活性，但也伴随着高风险。

> [!warning]
>
> ### 重要安全提示
>
> 插件在未经验证的情况下解析执行外部代码，存在较高的安全风险。执行用户输入的代码可能导致系统崩溃、数据泄露或其他不可预见的安全问题。
> 
> 因此，请确保只有可信赖的开发者被授予执行代码的权限。
>
> 使用本插件即表示您已理解并接受上述风险，并将进行严格的权限管理和安全防护。

## 💿 安装

<details open>
    <summary>使用 nb-cli 安装</summary>
    在 nonebot2 项目的根目录下打开命令行, 输入以下指令即可安装

    nb plugin install nonebot-plugin-exe-code

</details>

<details>
    <summary>使用包管理器安装</summary>
    在 nonebot2 项目的插件目录下, 打开命令行, 根据你使用的包管理器, 输入相应的安装命令

<details>
    <summary>pip</summary>

    pip install nonebot-plugin-exe-code

</details>

<details>
    <summary>pdm</summary>

    pdm add nonebot-plugin-exe-code

</details>

<details>
    <summary>poetry</summary>

    poetry add nonebot-plugin-exe-code

</details>

<details>
    <summary>conda</summary>

    conda install nonebot-plugin-exe-code

</details>

打开 nonebot2 项目根目录下的 `pyproject.toml` 文件, 在 `[tool.nonebot]` 部分追加写入

    plugins = ["nonebot_plugin_exe_code"]

</details>

## ⚙️ 配置

在 nonebot2 项目的`.env`文件中添加下表中的必填配置

|       配置项        | 必填 | 默认值 |                     说明                     |
| :-----------------: | :--: | :----: | :------------------------------------------: |
|  `exe_code__user`   |  否  |   无   |            允许执行代码的用户 ID             |
|  `exe_code__group`  |  否  |   无   |            允许执行代码的群组 ID             |
| `exe_code__qbot_id` |  否  |   无   | `OneBot V11` 发送 ark 卡片所需的官 Bot QQ 号 |

### 权限说明

对于 `exe_code__user` 中配置的用户，在私聊/任意群聊中均可触发命令。

对于 `exe_code__group` 中配置的群组，任意用户均可触发命令。

对于 NoneBot 默认配置项 `SUPERUSERS` 中配置的用户，在私聊/任意群聊中均可触发命令，且在执行环境中拥有额外管理权限。

## 🎉 使用

> [!note]
>
> 以下说明将假设您已掌握基础的 Python 异步编程语法。

### 命令概览

- `code [代码]` 在用户执行环境中执行代码。

  代码中包含的 `at` 消息段将被转换为 `用户ID` 字符串。

  代码中包含的 `图片` 消息段将被转换为 `图片URL` 字符串。

  具体参考 [`~depends:_ExtractCode`](./nonebot_plugin_exe_code/depends.py)

- `getraw` 获取引用消息的消息段的文本形式。

  例：对于 `OneBot V11` 适配器，将返回消息的 `CQ码`。

  提供变量： `gem`、`gurl`

- `getmid` 获取引用消息的消息 ID。

  提供变量： `gem`、`gurl`

- `getimg [varname]` 获取指定的图片。

  以 `PIL.Image.Image` 格式保存至上下文的 `[varname]` 变量中。未指定时默认为 `img`。

  提供变量： `gurl`

- `terminate [@someone]` 中止指定用户的代码。

  未指定时为自己的代码。仅 `SUPERUSERS` 可用。

> 对于上述 `getxxx` 命令，均可使用引用消息来指定传入的消息内容。
>
> `gem`: 传入消息内容的消息体，类型为适配器给出的消息类。
>
> `gurl`: 当传入消息包含图片时，自动提取的图片 URL。

### 执行环境

用户执行环境保存于 [`~code_context:Context._contexts`](./nonebot_plugin_exe_code/code_context.py)，随 NoneBot 重启而重置。

用户执行环境由 [`初始环境`](./nonebot_plugin_exe_code/interface/user_const_var.py) 深拷贝生成，包含 `UniMessage` 及一些常用消息段。

在传入代码开始执行前，用户执行环境将获得一个 [`API`](./nonebot_plugin_exe_code/interface/api.py) 实例，变量名固定为 `api`。同时，`qid` 变量将被设置为执行者的 `用户ID`，`gid` 变量将被设置为当前 `群组ID` (私聊则为 `None`)

`api` 中被 `@export` 装饰的方法将被导出到用户执行环境。例： `print`，`feedback`，`help`，...

传入的代码经过一次异步函数包装后，可以正常执行异步代码。具体参考 [`~code_context:Context._solve_code`](./nonebot_plugin_exe_code/code_context.py)。

对于供用户使用的接口方法，插件中使用 `@descript` 装饰器添加了描述。在执行代码时，可以通过 `await help(api.method)` 获取函数信息。

对于部分协议，插件提供了额外的接口，便于执行一些平台特化的操作。目前提供适配的协议：[`OneBot V11`](./nonebot_plugin_exe_code/interface/adapter_api/onebot11.py)、[`QQ`](./nonebot_plugin_exe_code/interface/adapter_api/qq.py)。

### 示例

```python
await feedback(At(qid) + " Hi there")   # 向当前会话发送消息
await user(qid).send(f"Hello {qid}!")   # 向指定用户发送消息
await group(gid).send(f"Hello {gid}!")  # 向指定群组发送消息

# 插件重写的 print 函数，用法同原 print
# print 的内容将写入缓冲区，在代码段执行结束后输出
print("test", end=" ")
print("NoneBot", "Plugin", sep="-")
```

## 📝 更新日志

<details>
    <summary>更新日志</summary>

- 2024.07.21 v1.0.1

  插件开源

</details>

## 鸣谢

- [nonebot/nonebot2](https://github.com/nonebot/nonebot2): 跨平台 Python 异步机器人框架
- [nonebot/plugin-alconna](https://github.com/nonebot/plugin-alconna): 跨平台的消息处理接口
- [noneplugin/nonebot-plugin-session](https://github.com/noneplugin/nonebot-plugin-session): 会话信息提取
