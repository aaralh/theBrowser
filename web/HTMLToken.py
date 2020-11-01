from enum import Enum, auto
from typing import Union, List, TypeVar
from dataclasses import dataclass, field


class HTMLToken:

    class TokenType(Enum):
        DOCTYPE = auto()
        StartTag = auto()
        EndTag = auto()
        Comment = auto()
        Character = auto()
        EOF = auto()

    def type(self) -> Union[TokenType, None]:
        return self.__type

    def __init__(self, tokenType: Union[TokenType, None]) -> None:
        self.__type = tokenType


class HTMLDoctype(HTMLToken):

    @dataclass
    class __Doctype:
        name: Union[str, None] = None
        publicIdentifier: Union[str, None] = None
        systemPublicIdentidier: Union[str, None] = None
        forcedQuircks: bool = False

    def __init__(self) -> None:
        self.__type = HTMLToken.TokenType.DOCTYPE
        self.doctype = self.__Doctype()

    def __str__(self) -> str:
        return f"type: {self.__type}, name: {self.doctype.name}"


class HTMLCommentOrCharacter(HTMLToken):

    @dataclass
    class __CommentOrCharacter:
        data: Union[str, None] = None

    def __init__(self, tokenType: HTMLToken.TokenType) -> None:
        self.__type = tokenType
        self.commentOrCharacter = self.__CommentOrCharacter()

    def __str__(self) -> str:
        return f"type: {self.__type}, name: {self.commentOrCharacter.data}"


class HTMLTag(HTMLToken):

    @dataclass
    class __Attribute:
        name: Union[str, None] = None
        value: Union[str, None] = None

    @dataclass
    class __Tag():
        name: Union[str, None] = None
        selfClosing: bool = False
        attributes: List["HTMLTag.__Attribute"] = field(
            default_factory=list)

    def __init__(self, tokenType: HTMLToken.TokenType) -> None:
        self.__type = tokenType
        self.tag = self.__Tag()

    def __str__(self) -> str:
        return f"type: {self.__type}, name: {self.tag.name}, attributes: {self.tag.attributes}"
