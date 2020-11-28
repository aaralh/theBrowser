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
    
    def __str__(self) -> str:
        return f"type: {self.__type}"


class HTMLDoctype(HTMLToken):

    def __init__(self) -> None:
        self.__type = HTMLToken.TokenType.DOCTYPE
        self.name: Union[str, None] = None
        self.publicIdentifier: Union[str, None] = None
        self.systemPublicIdentidier: Union[str, None] = None
        self.forcedQuircks: bool = False


    def __str__(self) -> str:
        return f"type: {self.__type}, name: {self.name}"


    def setName(self, newName: str) -> None:
        self.name = newName



class HTMLCommentOrCharacter(HTMLToken):

    def __init__(self, tokenType: HTMLToken.TokenType) -> None:
        self.__type = tokenType
        self.data: Union[str, None] = None

    def __str__(self) -> str:
        return f"type: {self.__type}, name: {self.data}"


class HTMLTag(HTMLToken):

    def __init__(self, tokenType: HTMLToken.TokenType) -> None:
        self.__type = tokenType
        self.activeAttributeName: Union[str, None] = None
        self.name: Union[str, None] = None
        self.selfClosing: bool = False
        self.attributes: Dict[str, str] = {}

    def __str__(self) -> str:
        return f"type: {self.__type}, name: {self.name}, attributes: {self.attributes}"


    def createNewAttribute(self) -> None:
        self.attributes[""] = ""
        self.activeAttributeName = ""
    
    def addCharToAttributeName(self, char: str) -> None:
        if (self.activeAttributeName == None):
            return
        self.attributes[self.activeAttributeName + char] = self.attributes[self.activeAttributeName]
        del self.attributes[self.activeAttributeName]
        self.activeAttributeName += char
    
    def addCharToAttributeValue(self, char: str) -> None:
        if (self.activeAttributeName == None):
            return
            
        self.attributes[self.activeAttributeName] = self.attributes[self.activeAttributeName] + char