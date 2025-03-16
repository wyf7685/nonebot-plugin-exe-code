import functools
from collections.abc import Generator
from typing import ClassVar, NamedTuple, Self

from ..typings import T_Context
from .help_doc import MethodDescription
from .user_const_var import BUILTINS_KEY, DEFAULT_BUILTINS
from .utils import get_method_description, is_export_method


class _Desc(NamedTuple):
    inst_name: str
    func_name: str
    is_export: bool
    description: str


class Interface:
    __slots__ = ("__builtins", "__context", "__exported")

    __inst_name__: ClassVar[str] = "interface"
    __export_method__: ClassVar[set[str]] = set()
    __method_description__: ClassVar[set[MethodDescription]] = set()

    __builtins: dict[str, object] | None
    __context: T_Context | None
    __exported: set[str]

    def __init__(self, context: T_Context | None = None) -> None:
        self.__builtins = DEFAULT_BUILTINS.copy() if context is not None else None
        self.__context = context
        self.__exported = set()

    def __init_subclass__(cls) -> None:
        # e.g.: User[xxx]
        #   --> AttributeError: type object 'User' has no attribute '__parameters__'
        if type_params := getattr(cls, "__type_params__", None):
            cls.__parameters__ = type_params  # type: ignore[reportAttributeAccessIssue]

        if cls.__inst_name__ == Interface.__inst_name__:
            cls.__inst_name__ = cls.__name__.lower()  # pragma: no cover
        cls.__export_method__ = {
            name for name, value in cls.__dict__.items() if is_export_method(value)
        }
        cls.__method_description__ = {
            desc
            for value in cls.__dict__.values()
            if (desc := get_method_description(value))
        }

    def _export(self, key: str, val: object) -> None:
        if self.__builtins is None:  # pragma: no cover
            raise TypeError(
                f"Interface class {type(self).__name__!r} not allowed to export"
            )
        self.__builtins[key] = val
        self.__exported.add(key)

    def export(self) -> None:
        self._export(self.__inst_name__, self)
        for name in self._get_export_method():
            self._export(name, getattr(self, name))

    def __enter__(self) -> Self:
        assert self.__context is not None
        assert self.__builtins is not None

        self.export()
        self.__context[BUILTINS_KEY] = self.__builtins
        return self

    def __exit__(self, *_: object) -> bool:
        if _builtins := self.__builtins:
            for name in self.__exported:
                _builtins.pop(name, None)
        return False

    async def __aenter__(self) -> Self:
        return self.__enter__()

    async def __aexit__(self, *_: object) -> bool:
        return self.__exit__(*_)

    @classmethod
    def _get_export_method(cls) -> Generator[str, None, None]:
        yield from functools.reduce(
            set[str].union,
            (c.__export_method__ for c in cls.mro() if issubclass(c, Interface)),
            set(),
        )

    @classmethod
    def get_all_description(cls) -> tuple[list[str], list[str]]:
        method_dict: dict[str, _Desc] = {}
        for c in cls.mro():
            if issubclass(c, Interface):
                for d in c.__method_description__:
                    desc = _Desc(
                        inst_name=cls.__inst_name__,
                        func_name=d.name,
                        is_export=is_export_method(d.call),
                        description=d.format(),
                    )
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
