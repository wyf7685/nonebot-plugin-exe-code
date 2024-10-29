# ruff: noqa: N818
"""
Error
├── ContextError
│   ├── SessionNotInitialized
│   └── BotEventMismatch
└── APIError
    ├── APICallFailed
    ├── ParamError
    │   ├── ParamMismatch
    │   └── ParamMissing
    └── NoMethodDescription
"""

from typing import Any


class Error(Exception):
    def __init__(self, msg: str | None = None, **data: Any) -> None:
        super().__init__()
        self.msg = msg
        self.data = data

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.msg}" + "".join(
            f", {k}={v}" for k, v in self.data.items()
        )


class ContextError(Error): ...


class SessionNotInitialized(ContextError): ...


class BotEventMismatch(ContextError): ...


class APIError(Error): ...


class APICallFailed(APIError): ...


class ParamError(APIError, TypeError): ...


class ParamMismatch(ParamError): ...


class ParamMissing(ParamError): ...


class NoMethodDescription(APIError): ...
