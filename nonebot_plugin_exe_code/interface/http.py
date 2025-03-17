# ruff: noqa: A005
import functools
from collections.abc import Mapping
from http.cookiejar import CookieJar
from typing import IO, Self, override

from multidict import CIMultiDict
from nonebot import get_driver
from nonebot.drivers import HTTPClientMixin
from nonebot.internal.driver.model import (
    Cookies,
    Request,
    Response,
)
from yarl import URL

from .decorators import debug_log, strict
from .help_doc import descript
from .interface import Interface

SimpleQuery = str | int | float
QueryTypes = (
    None
    | str
    | Mapping[str, SimpleQuery | list[SimpleQuery]]
    | list[tuple[str, SimpleQuery]]
)
HeaderTypes = None | CIMultiDict[str] | dict[str, str] | list[tuple[str, str]]
CookieTypes = None | Cookies | CookieJar | dict[str, str] | list[tuple[str, str]]
ContentTypes = str | bytes | None
DataTypes = dict[str, object] | None
FileContent = IO[bytes] | bytes
FileTypes = (
    FileContent
    | tuple[str | None, FileContent]
    | tuple[str | None, FileContent, str | None]
)
FilesTypes = dict[str, FileTypes] | list[tuple[str, FileTypes]] | None


_PARAMETER_DESCRIPTION = dict(
    # method="请求方法",
    url="请求地址",
    params="请求参数",
    headers="请求头",
    cookies="请求 cookies",
    content="请求内容",
    data="请求数据",
    json="请求 JSON 数据",
    files="上传文件",
)


class WrappedResponse:
    status_code: int
    headers: CIMultiDict[str]
    content: ContentTypes
    request: Request | None

    def __init__(self, response: Response) -> None:
        self._response = response

    def __getattr__(self, name: str) -> object:
        return getattr(self._response, name)

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    def raise_for_status(self) -> Self:
        if not self.ok:
            raise RuntimeError(f"Request failed with status code {self.status_code}")
        return self

    def read(self) -> bytes:
        return (
            self.content.encode()
            if isinstance(self.content, str)
            else self.content or b""
        )

    @override
    def __repr__(self) -> str:  # pragma: no cover
        return repr(self._response)


class Http(Interface):
    __slots__ = ("__dict__",)

    @functools.cached_property
    def _http(self) -> HTTPClientMixin:
        driver = get_driver()
        if not isinstance(driver, HTTPClientMixin):  # pragma: no cover
            raise TypeError(
                f"Current driver {driver} does not support http client requests"
            )
        return driver

    @descript(
        description="发送 HTTP 请求",
        parameters=dict(
            method="请求方法",
            **_PARAMETER_DESCRIPTION,
        ),
        result="请求响应",
    )
    @debug_log
    @strict
    async def request(
        self,
        method: str | bytes,
        url: URL | str,
        *,
        params: QueryTypes = None,
        headers: HeaderTypes = None,
        cookies: CookieTypes = None,
        content: ContentTypes = None,
        data: DataTypes = None,
        json: object = None,
        files: FilesTypes = None,
    ) -> WrappedResponse:
        setup = Request(
            method=method,
            url=url,
            params=params,
            headers=headers,
            cookies=cookies,
            content=content,
            data=data,
            json=json,
            files=files,
        )
        return WrappedResponse(await self._http.request(setup))

    @descript(
        description="发送 GET 请求",
        parameters=_PARAMETER_DESCRIPTION.copy(),
        result="请求响应",
    )
    async def get(
        self,
        url: URL | str,
        *,
        params: QueryTypes = None,
        headers: HeaderTypes = None,
        cookies: CookieTypes = None,
        content: ContentTypes = None,
        data: DataTypes = None,
        json: object = None,
        files: FilesTypes = None,
    ) -> WrappedResponse:
        return await self.request(
            "GET",
            url,
            params=params,
            headers=headers,
            cookies=cookies,
            content=content,
            data=data,
            json=json,
            files=files,
        )

    @descript(
        description="发送 POST 请求",
        parameters=_PARAMETER_DESCRIPTION.copy(),
        result="请求响应",
    )
    async def post(
        self,
        url: URL | str,
        *,
        params: QueryTypes = None,
        headers: HeaderTypes = None,
        cookies: CookieTypes = None,
        content: ContentTypes = None,
        data: DataTypes = None,
        json: object = None,
        files: FilesTypes = None,
    ) -> WrappedResponse:
        return await self.request(
            "POST",
            url,
            params=params,
            headers=headers,
            cookies=cookies,
            content=content,
            data=data,
            json=json,
            files=files,
        )
