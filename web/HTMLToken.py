from enum import Enum, auto
from typing import Union, List, TypeVar
from dataclasses import dataclass, field

class HTMLToken:

	@dataclass
	class __CommentOrCharacter:
		data: Union[str, None] = None

	@dataclass
	class __Attribute:
		name: Union[str, None] = None
		value: Union[str, None] = None

	@dataclass
	class __Doctype:
		name: Union[str, None] = None
		publicIdentifier: Union[str, None] = None
		systemPublicIdentidier: Union[str, None] = None
		forcedQuircks: bool = False
	
	@dataclass
	class __Tag:
		name: Union[str, None] = None
		selfClosing: bool = False
		attributes: List[TypeVar("HTMLToken.__Attribute")] = field(default_factory=list)
		

	def __init__(self):
		self.__type = None
		self.__doctype = self.__Doctype()


	class TokenType(Enum):
		DOCTYPE = auto()
		StartTag = auto()
		EndTag = auto()
		Comment = auto()
		Character = auto()
		EOF = auto()
	
	def type(self) -> Union[TokenType, None]:
		return self.__type
