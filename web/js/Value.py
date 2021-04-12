import enum
from typing import Any

from libs.MetaClasses import MultipleMeta


class Value(metaclass=MultipleMeta):

    class Type(enum.Enum):
        Undefined = enum.auto(),
        Null = enum.auto(),
        Number = enum.auto(),
        String = enum.auto(),
        Object = enum.auto(),
        Symbol = enum.auto(),
        BigInt = enum.auto(),
        Boolean = enum.auto(),
        Function = enum.auto()

    def __init__(self, value: Any) -> None:
        self.__type = self.__get_type(value)
        self.__value = value

    def __init__(self, value_type: Type) -> None:
        self.__init__(None)
        self.__type = value_type

    def __get_type(self, value: Any):
        types = {
            bool: self.Type.Boolean,
            int: self.Type.Number,
            type(None): self.Type.Null,
            str: self.Type.String,
            dict: self.Type.Object
        }
        return types.get(type(value), self.Type.Undefined)

    @property
    def type(self) -> Type:
        return self.__type

    @property
    def value(self) -> Type:
        return self.__value


def js_undefiend() -> Value:
    return Value(value_type=Value.Type.Undefined)


def js_null() -> Value:
    return Value(value_type=Value.Type.Null)