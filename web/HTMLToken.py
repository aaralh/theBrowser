from enum import Enum, auto
from typing import Union, Dict
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
    class __Tag():
        name: Union[str, None] = None
        selfClosing: bool = False
        attributes: Dict[str, str] = field(default_factory=dict)

    def __init__(self, tokenType: HTMLToken.TokenType) -> None:
        self.__type = tokenType
        self.tag = self.__Tag()
        self.activeAttributeName: Union[str, None] = None

    def __str__(self) -> str:
        return f"type: {self.__type}, name: {self.tag.name}, attributes: {self.tag.attributes}"


    def createNewAttribute(self) -> None:
        self.tag.attributes[""] = ""
        self.activeAttributeName = ""
    
    def addCharToAttributeName(self, char: str) -> None:
        if (self.activeAttributeName == None):
            return
        self.tag.attributes[self.activeAttributeName + char] = self.tag.attributes[self.activeAttributeName]
        del self.tag.attributes[self.activeAttributeName]
        self.activeAttributeName += char
    
    def addCharToAttributeValue(self, char: str) -> None:
        if (self.activeAttributeName == None):
            return
            
        self.tag.attributes[self.activeAttributeName] = self.tag.attributes[self.activeAttributeName] + char