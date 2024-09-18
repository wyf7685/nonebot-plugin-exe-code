from collections.abc import Callable, Generator
from typing import Any, ClassVar, NamedTuple, cast

from ..constant import INTERFACE_INST_NAME, INTERFACE_METHOD_DESCRIPTION, T_Context
from .help_doc import FuncDescription
from .utils import is_export_method


class _Desc(NamedTuple):
    inst_name: str
    func_name: str
    is_export: bool
    description: str


class InterfaceMeta(type):
    __export_method__: list[str]
    __method_description__: dict[str, FuncDescription]

    def __new__(  # noqa: ANN204
        cls, name: str, bases: tuple[type, ...], attrs: dict[str, Any]
    ):
        # default instance name
        attrs.setdefault(INTERFACE_INST_NAME, name.lower())

        Interface = super().__new__(cls, name, bases, attrs)  # noqa: N806
        attr = Interface.__dict__  # shortcut

        # export
        Interface.__export_method__ = [
            name for name, value in attr.items() if is_export_method(value)
        ]

        # description
        Interface.__method_description__ = {
            name: desc
            for name, value in attr.items()
            if (desc := getattr(value, INTERFACE_METHOD_DESCRIPTION, None))
        }

        return Interface

    def get_export_method(cls) -> Generator[str, None, None]:
        for c in reversed(cls.mro()):
            if isinstance(c, InterfaceMeta) and hasattr(c, "__export_method__"):
                yield from c.__export_method__

    def _get_method_description(cls) -> Generator[_Desc, None, None]:
        inst_name: str = cls.__inst_name__  # pyright:ignore[reportAttributeAccessIssue]
        for func_name, desc in cls.__method_description__.items():
            func = cast(Callable[..., Any], getattr(cls, func_name))
            is_export = is_export_method(func)
            yield _Desc(inst_name, func_name, is_export, desc.format(func))


class Interface(metaclass=InterfaceMeta):
    __inst_name__: ClassVar[str] = "interface"
    __export_method__: ClassVar[list[str]]
    __method_description__: ClassVar[dict[str, str]]

    def export_to(self, context: T_Context) -> None:
        for name in type(self).get_export_method():
            context[name] = getattr(self, name)
        context[self.__inst_name__] = self

    @classmethod
    def _get_all_description(cls) -> tuple[list[str], list[str]]:
        methods: list[_Desc] = []
        for c in cls.mro():
            if issubclass(c, Interface):
                methods.extend(c._get_method_description())  # noqa: SLF001
        methods.sort(key=lambda x: (1 - x.is_export, x.inst_name, x.func_name))

        content: list[str] = []
        result: list[str] = []
        for index, desc in enumerate(methods, 1):
            prefix = f"{index}. "
            if not desc.is_export:
                prefix += f"{desc.inst_name}."
            content.append(prefix + desc.func_name)
            result.append(prefix + desc.description)

        return content, result
