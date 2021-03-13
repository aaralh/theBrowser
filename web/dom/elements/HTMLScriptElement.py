from typing import Union
from web.dom.Document import Document
from web.dom.elements.Element import Element

class HTMLScriptElement(Element):
	def __init__(self, *args: str, **kwargs: int) -> None:
		super(HTMLScriptElement, self).__init__(*args, **kwargs)
		self.__parserDocument: Union[Document, None] = None
		self.__isNonBlocking: bool = False

	@property
	def parserDocument(self) -> Document:
		return self.__parserDocument

	@parserDocument.setter
	def parserDocument(self, document: Document) -> None:
		self.__parserDocument = document

	@property
	def isNonBlocking(self) -> bool:
		return self.__isNonBlocking

	@isNonBlocking.setter
	def isNonBlocking(self, isBlocking: bool) -> None:
		self.__isNonBlocking = isBlocking
