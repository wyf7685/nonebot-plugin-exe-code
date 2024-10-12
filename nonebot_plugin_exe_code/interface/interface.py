from collections.abc import Callable, Generator
from typing import Any, ClassVar, NamedTuple, cast

from typing_extensions import Self

from ..typings import T_Context
from .help_doc import MethodDescription
from .utils import get_method_description, is_export_method


class _Desc(NamedTuple):
    inst_name: str
    func_name: str
    is_export: bool
    description: str


class Interface:
    __inst_name__: ClassVar[str] = "interface"
    __export_method__: ClassVar[list[str]] = []
    __method_description__: ClassVar[dict[str, MethodDescription]] = {}

    __slots__ = ("__context", "__exported")

    __context: T_Context | None
    __exported: set[str]

    def __init__(self, context: T_Context | None = None) -> None:
        self.__context = context
        self.__exported = set()

    def __init_subclass__(cls) -> None:
        if cls.__inst_name__ == Interface.__inst_name__:
            cls.__inst_name__ = cls.__name__.lower()  # pragma: no cover
        cls.__export_method__ = [
            name for name, value in cls.__dict__.items() if is_export_method(value)
        ]
        cls.__method_description__ = {
            name: desc
            for name, value in cls.__dict__.items()
            if (desc := get_method_description(value))
        }

    def _export(self, key: str, val: Any) -> None:
        if self.__context is None:  # pragma: no cover
            raise TypeError(
                f"Interface class {type(self).__name__!r} not allowed to export"
            )
        self.__context[key] = val
        self.__exported.add(key)

    def export(self) -> None:
        self._export(self.__inst_name__, self)
        for name in self._get_export_method():
            self._export(name, getattr(self, name))

    def __enter__(self) -> Self:
        self.export()
        return self

    def __exit__(self, *_: object) -> bool:
        if self.__context is not None:
            for name in self.__exported:
                self.__context.pop(name, None)
        return False

    async def __aenter__(self) -> Self:
        return self.__enter__()

    async def __aexit__(self, *_: object) -> bool:
        return self.__exit__(*_)

    @classmethod
    def _get_export_method(cls) -> Generator[str, None, None]:
        for c in reversed(cls.mro()):
            if issubclass(c, Interface):
                yield from c.__export_method__

    @classmethod
    def _get_method_description(cls) -> Generator[_Desc, None, None]:
        for func_name, desc in cls.__method_description__.items():
            func = cast(Callable[..., Any], getattr(cls, func_name))
            is_export = is_export_method(func)
            yield _Desc(
                inst_name=cls.__inst_name__,
                func_name=func_name,
                is_export=is_export,
                description=desc.format(),
            )

    @classmethod
    def get_all_description(cls) -> tuple[list[str], list[str]]:
        method_dict: dict[str, _Desc] = {}
        for c in cls.mro():
            if issubclass(c, Interface):
                for desc in c._get_method_description():  # noqa: SLF001
                    method_dict.setdefault(desc.func_name, desc)
        methods = sorted(
            method_dict.values(),
            key=lambda x: (1 - x.is_export, x.inst_name, x.func_name),
        )

        content: list[str] = []
        result: list[str] = []
        for index, desc in enumerate(methods, 1):
            prefix = f"{index}. "
            if not desc.is_export:
                prefix += f"{desc.inst_name}."
            content.append(prefix + desc.func_name)
            result.append(prefix + desc.description)

        return content, result
