<div align="center">
  <a href="https://v2.nonebot.dev/store">
    <img src="https://github.com/wyf7685/wyf7685/blob/main/assets/NoneBotPlugin.svg" width="300" alt="logo">
  </a>
</div>

<div align="center">

# nonebot-plugin-exe-code

_✨ 在聊天中执行带有上下文的 Python 代码 ✨_

[![license](https://img.shields.io/github/license/wyf7685/nonebot-plugin-exe-code.svg)](./LICENSE)
[![pypi](https://img.shields.io/pypi/v/nonebot-plugin-exe-code?logo=python&logoColor=edb641)](https://pypi.python.org/pypi/nonebot-plugin-exe-code)
[![python](https://img.shields.io/badge/python-3.10+-blue?logo=python&logoColor=edb641)](https://www.python.org/)

[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![isort](https://img.shields.io/badge/%20imports-isort-%231674b1)](https://pycqa.github.io/isort/)
[![black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![pyright](https://img.shields.io/badge/types-pyright-797952.svg?logo=python&logoColor=edb641)](https://github.com/Microsoft/pyright)
[![ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

[![commits](https://img.shields.io/github/commit-activity/w/wyf7685/nonebot-plugin-exe-code)](https://github.com/wyf7685/nonebot-plugin-exe-code/commits)
[![codecov](https://codecov.io/gh/wyf7685/nonebot-plugin-exe-code/graph/badge.svg?token=5T85DTD4FG)](https://codecov.io/gh/wyf7685/nonebot-plugin-exe-code)
[![pre-commit](https://results.pre-commit.ci/badge/github/wyf7685/nonebot-plugin-exe-code/master.svg)](https://results.pre-commit.ci/latest/github/wyf7685/nonebot-plugin-exe-code/master)
[![pyright](https://github.com/wyf7685/nonebot-plugin-exe-code/actions/workflows/pyright.yml/badge.svg?branch=master&event=push)](https://github.com/wyf7685/nonebot-plugin-exe-code/actions/workflows/pyright.yml)
[![publish](https://github.com/wyf7685/nonebot-plugin-exe-code/actions/workflows/pypi-publish.yml/badge.svg)](https://github.com/wyf7685/nonebot-plugin-exe-code/actions/workflows/pypi-publish.yml)

[![NoneBot Registry](https://img.shields.io/endpoint?url=https%3A%2F%2Fnbbdg.lgc2333.top%2Fplugin%2Fnonebot-plugin-exe-code)](https://registry.nonebot.dev/plugin/nonebot-plugin-exe-code:nonebot_plugin_exe_code)
[![Supported Adapters](https://img.shields.io/endpoint?url=https%3A%2F%2Fnbbdg.lgc2333.top%2Fplugin-adapters%2Fnonebot-plugin-exe-code)](https://registry.nonebot.dev/plugin/nonebot-plugin-exe-code:nonebot_plugin_exe_code)

</div>

## 📖 介绍

本插件旨在允许开发者在聊天中执行带有上下文的 Python 代码，从而对 NoneBot 框架进行运行时侵入式修改。

由于这种设计，插件具有极高的灵活性，但也伴随着高风险。

> [!warning]
>
> ### 🚨 重要安全提示
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

在 nonebot2 项目的 `.env` 文件中添加下表中的配置

|      配置项       | 必填 | 默认值 |         说明          |
| :---------------: | :--: | :----: | :-------------------: |
| `exe_code__user`  |  否  |   []   | 允许执行代码的用户 ID |
| `exe_code__group` |  否  |   []   | 允许执行代码的群组 ID |

<details>
  <summary>可选配置</summary>

插件为 `OneBot V11` 适配器封装了发送 [`QQ官方机器人`](https://bot.q.qq.com/wiki/develop/api-v2/) 的 [`ark卡片消息`](https://bot.q.qq.com/wiki/develop/api-v2/server-inter/message/type/ark.html) 的接口，参考 [`这里`](https://github.com/wyf7685/nonebot-plugin-exe-code/blob/master/nonebot_plugin_exe_code/interface/adapter_api/onebot11.py#L59-L99)

使用时需要在 `.env` 文件中添加如下配置，在 nonebot2 项目中配置 `OneBot V11` 适配器和 `QQ` 适配器，并连接到两个对应的 Bot 账号，并确保两者之间可以发送私聊消息。

|          配置项          | 必填 | 默认值 |                     说明                     |
| :----------------------: | :--: | :----: | :------------------------------------------: |
|   `exe_code__qbot_id`    |  是  |   无   | `OneBot V11` 发送 ark 卡片所需的官 Bot QQ 号 |
| `exe_code__qbot_timeout` |  否  |  30.0  |   `OneBot V11` 发送 ark 卡片的超时时长(秒)   |

</details>

### 📄 权限说明

对于 `exe_code__user` 中配置的用户，在私聊/任意群聊中均可触发命令。

对于 `exe_code__group` 中配置的群组，任意用户均可触发命令。

对于 NoneBot 默认配置项 [`SUPERUSERS`](https://nonebot.dev/docs/appendices/config#superusers) 中配置的用户，在私聊/任意群聊中均可触发命令，且在执行环境中拥有额外管理权限。

### 📦️ 数据存储

插件使用 [`nonebot/plugin-localstore`](https://github.com/nonebot/plugin-localstore) 存储用户数据，存储位置参考 [`这里`](https://github.com/nonebot/plugin-localstore?tab=readme-ov-file#%E5%AD%98%E5%82%A8%E8%B7%AF%E5%BE%84)

## 🎉 使用

> [!note]
>
> 以下说明将假设您已掌握基础的 Python 异步编程语法。

### 命令概览

- `code [代码]` 在用户执行环境中执行代码。

  代码中包含的 `at` 消息段将被转换为 `用户ID` 字符串。

  代码中包含的 `图片` 消息段将被转换为 `图片URL` 字符串。

  具体处理逻辑参考 [`~matchers.depends:_ExtractCode`](./nonebot_plugin_exe_code/matchers/depends.py)

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

> [!note]
>
> 对于上述 `getxxx` 命令，均可使用引用消息来指定传入的消息内容。

> [!note]
>
> `gem`: 传入消息内容的消息体，类型为适配器给出的消息类。
>
> `gurl`: 当传入消息包含图片时，自动提取的图片 URL。

### 执行环境

用户执行环境保存于 [`~context:Context._contexts`](./nonebot_plugin_exe_code/context.py)，随 NoneBot 重启而重置。

用户执行环境由 [`初始环境`](./nonebot_plugin_exe_code/interface/user_const_var.py) 深拷贝生成，包含 `UniMessage` 及一些常用消息段。

在传入代码开始执行前，用户执行环境将获得一个 [`API`](./nonebot_plugin_exe_code/interface/api.py) 实例，变量名固定为 `api`。同时，`qid` 变量将被设置为执行者的 `用户ID`，`gid` 变量将被设置为当前 `群组ID` (私聊则为 `None`)

`api` 中被 `@export` 装饰的方法将被导出到用户执行环境。例： `print`，`feedback`，`help`，`input`，...

传入的代码经过一次异步函数包装后，可以正常执行异步代码。具体参考 [`~context:Context._solve_code`](./nonebot_plugin_exe_code/context.py)。

对于供用户使用的接口方法，插件中使用 `@descript` 装饰器添加了描述。在执行代码时，可以通过 `await help(api.method)` 获取函数信息。

对于部分协议，插件提供了额外的接口，便于执行一些平台特化的操作。目前提供适配的协议：[`OneBot V11`](./nonebot_plugin_exe_code/interface/adapter_api/onebot11.py)、[`QQ`](./nonebot_plugin_exe_code/interface/adapter_api/qq.py)。

### 示例

```python
await feedback(At(qid) + " Hi there")  # 向当前会话发送消息
await user(qid).send(f"Hello {qid}")   # 向指定用户发送消息
await group(gid).send(f"Hello {gid}")  # 向指定群组发送消息

# 插件重写的 print 函数，用法同原 print
# print 的内容将写入缓冲区，在代码段执行结束后输出
print("test", end=" ")
print("NoneBot", "Plugin", sep="-")

# 使用 UniMessage 提供的 Receipt 操作发送的消息
receipt = await feedback("Recall in 3s...")
await sleep(3)          # 异步等待 3 秒
await receipt.recall()  # 撤回消息
```

## 📝 更新日志

<details>
    <summary>更新日志</summary>
  
<!-- CHANGELOG -->

- 2024.10.12 v1.1.4

  - 重构 descript 装饰器
  - OneBot V11 上传文件接口指定超时时间
  - Interface 及其子类添加 __slots__

- 2024.10.10 v1.1.3

  - 增加参数类型校验
  - 重构合并转发相关代码
  - 将 send_fwd 函数移动至 ob11 api
  - 调整插件结构
  - 修正错误处理

- 2024.10.02 v1.1.2

  - 支持代码内使用 yield 返回多个值
  - get 类命令加锁
  - 执行结束删除导出变量
  - 修改 SUPERUERS 管理函数格式
  - ob11 & satori 可使用 `api.mid` 快捷获取 message_id
  - ob11 & satori 接口: set_reaction

- 2024.09.22 v1.1.1

  - 优化平台消息类型获取
  - 重命名 ob11 群禁言接口: `set_ban` -> `set_mute`
  - 新增 satori 接口: 群禁言
  - 新增 ob11 接口: 上传文件
  - 移除依赖 userinfo
  - 使用 session 作为用户标识

- 2024.09.07 v1.1.0

  - `OneBot V11` 适配器接口: 群名片, 群禁言, 资料卡点赞
  - 修复鉴权错误

- 2024.08.24 v1.0.9

  - 修复 `User.send_fwd` 的 `target` 错误
  - 修复 `SendArk` 的 `ark_37` 参数错误
  - 优化 `getimg` 提取图片逻辑, 限制回复提取递归次数

- 2024.08.09 v1.0.8

  - 使用 `Permission` 判断执行权限 (原为 `Rule`)
  - 降低 [`nonebot/plugin-localstore`](https://github.com/nonebot/plugin-localstore) 版本需求为 `>=0.6.0`

- 2024.08.09 v1.0.7

  - 使用 [`nonebot/plugin-localstore`](https://github.com/nonebot/plugin-localstore) 存储插件数据
  - 回滚 `v1.0.4` 的消息发送接口修改
  - 修改 Python 版本需求为 `>=3.10`

- 2024.08.04 v1.0.6

  - `Context` 添加字典操作
  - `input` 函数改为返回 `UniMessage`, 超时改为抛出 `TimeoutError`
  - 修复 `help` 函数获取单个方法信息时, 实例名显示错误
  - `API._native_send` 改为返回平台接口数据

- 2024.08.01 v1.0.5

  - 新增函数 `input`, 用于从对话中获取输入

- 2024.08.01 v1.0.4

  - 发送消息类接口改为返回 Task, 允许不等待消息返回

  - `api.set_const` 变量名添加 isidentifier 校验

- 2024.07.21 v1.0.2

  - 修复消息混排处理

- 2024.07.21 v1.0.1

  - 插件开源

</details>

## 鸣谢

- [`nonebot/nonebot2`](https://github.com/nonebot/nonebot2): 跨平台 Python 异步机器人框架
- [`nonebot/plugin-alconna`](https://github.com/nonebot/plugin-alconna): 跨平台的消息处理接口
- [`nonebot/plugin-localstore`](https://github.com/nonebot/plugin-localstore): 插件数据存储
- [`noneplugin/nonebot-plugin-session`](https://github.com/noneplugin/nonebot-plugin-session): 会话信息提取
- [`RF-Tar-Railt/nonebot-plugin-waiter`](https://github.com/RF-Tar-Railt/nonebot-plugin-waiter): 灵活获取用户输入
