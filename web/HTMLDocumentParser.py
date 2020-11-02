from enum import Enum, auto
from typing import Any, List, Union
from web.HTMLToken import HTMLToken
from web.HTMLTokenizer import HTMLTokenizer

class Node():
	def __init__(self):
		self.title = "Node"

class HTMLDocumentParser:

	class __Mode(Enum):
		Initial = auto()
		BeforeHTML = auto()
		BeforeHead = auto()
		InHead = auto()
		InHeadNoscript = auto()
		AfterHead = auto()
		InBody = auto()
		Text = auto()
		InTable = auto()
		InTableText = auto()
		InCaption = auto()
		InColumnGroup = auto()
		InTableBody = auto()
		InRow = auto()
		InCell = auto()
		InSelect = auto()
		InSelectInTable = auto()
		InTemplate = auto()
		AfterBody = auto()
		InFrameset = auto()
		AfterFrameset = auto()
		AfterAfterBody = auto()
		AfterAfterFrameset = auto()


	def __init__(self, html: str) -> None:
		self.__currentInsertionMode = self.__Mode.Initial
		self.__openElements: List[Node] = []
		self.__tokenizer = HTMLTokenizer(html, self.__tokenHandler)

	def __tokenHandler(self, token: Any) -> None:
		print(token)

	def currentInsertionMode(self) -> __Mode:
		return self.__currentInsertionMode

	def nextToken(self) -> Union[HTMLToken, None]:
		return 

	
	def run(self) -> None:
		self.__tokenizer.run()

