from enum import Enum, auto
from typing import Optional, Dict
from dataclasses import dataclass, field


class HTMLToken:
    class TokenType(Enum):
        DOCTYPE = auto()
        StartTag = auto()
        EndTag = auto()
        Comment = auto()
        Character = auto()
        EOF = auto()

    @property
    def type(self) -> Optional[TokenType]:
        return self.__type

    def __init__(self, tokenType: Optional[TokenType]) -> None:
        self.__type = tokenType

    def __str__(self) -> str:
        return f"type: {self.__type}"


class HTMLDoctype(HTMLToken):

    def __init__(self) -> None:
        super(HTMLDoctype, self).__init__(HTMLToken.TokenType.DOCTYPE)
        self.name: Optional[str] = None
        self.publicIdentifier: Optional[str] = None
        self.systemPublicIdentidier: Optional[str] = None
        self.forcedQuircks: bool = False

    def __str__(self) -> str:
        return f"type: {self.type}, name: {self.name}"

    def setName(self, newName: str) -> None:
        self.name = newName


class HTMLCommentOrCharacter(HTMLToken):

    def __init__(self, tokenType: HTMLToken.TokenType) -> None:
        super(HTMLCommentOrCharacter, self).__init__(tokenType)
        self.data: Optional[str] = None

    def __str__(self) -> str:
        return f"type: {self.type}, name: {self.data}"

    def is_parser_white_space(self):
        return self.data.isspace()


class HTMLTag(HTMLToken):

    def __init__(self, tokenType: HTMLToken.TokenType) -> None:
        super(HTMLTag, self).__init__(tokenType)
        self.activeAttributeName: Optional[str] = None
        self.name: Optional[str] = None
        self.selfClosing: bool = False
        self.attributes: Dict[str, str] = {}

    def __str__(self) -> str:
        return f"type: {self.type}, name: {self.name}, attributes: {self.attributes}"

    def create_new_attribute(self) -> None:
        self.attributes[""] = ""
        self.activeAttributeName = ""

    def add_char_to_attribute_name(self, char: str) -> None:
        if self.activeAttributeName is None:
            return
        self.attributes[self.activeAttributeName + char] = self.attributes[self.activeAttributeName]
        del self.attributes[self.activeAttributeName]
        self.activeAttributeName += char

    def add_char_to_attribute_value(self, char: str) -> None:
        if self.activeAttributeName is None:
            return

        self.attributes[self.activeAttributeName] = self.attributes[self.activeAttributeName] + char

    def append_char_to_token_name(self, char: str) -> None:
        if self.name is None:
            self.name = char
        else:
            self.name += char
