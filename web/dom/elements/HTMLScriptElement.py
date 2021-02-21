from typing import Union
from web.dom.Document import Document
from web.dom.elements.Element import Element

class HTMLScriptElement(Element):
	def __init__(self, *args, **kwargs):
		super(HTMLScriptElement, self).__init__(*args, **kwargs)
		self._parserDocument: Union[Document, None] = None
		self._isNonBlocking: bool = False

	@property
	def parserDocument(self) -> Document:
		return self._parserDocument

	@parserDocument.setter
	def parserDocument(self, document: Document) -> None:
		self._parserDocument = document

	@property
	def isNonBlocking(self) -> bool:
		return self._isNonBlocking

	@parserDocument.setter
	def isNonBlocking(self, isBlocking: bool) -> None:
		self._isNonBlocking = isBlocking