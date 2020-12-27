
from dataclasses import dataclass
from typing import List, Union

from web.dom.elements.Element import Element
from web.html.parser.ParserUtils import ParserUtils


class StackOfOpenElments:


	@dataclass
	class LastElementResult:
		index: Union[int, None] = None
		element: Union[Element, None] = None

	def __init__(self):
		self.__openElements: List[Element] = []
		self.__scopeBaseList: List[str] = ["applet", "caption", "html", "table", "td", "th", "marquee", "object", "template"]

	def __hasInScopeImpl(self, targetNodeName: str, tagNameList: List[str]) -> bool:
		for node in reversed(self.__openElements):
			if (node.name == targetNodeName):
				return True
			if (node.name in tagNameList):
				return False

	def popAllElements(self) -> None:
		while not self.isEmpty():
			self.__openElements.pop()

	def isEmpty(self) -> bool:
		return len(self.__openElements) == 0

	def first(self) -> Union[Element, None]:
		if (not self.isEmpty()):
			return self.__openElements[0]
		return None

	def last(self) -> Union[Element, None]:
		if (not self.isEmpty()):
			return self.__openElements[-1]
		return None

	def push(self, element: Element) -> None:
		self.__openElements.append(element)

	def pop(self) -> Union[Element, None]:
		if (not self.isEmpty()):
			return self.__openElements.pop()
		return None

	def currentNode(self) -> Union[Element, None]:
		return self.last()

	def hasInScope(self, tagName: str) -> bool:
		return self.__hasInScopeImpl(tagName, self.__scopeBaseList)

	def hasInButtonScope(self, tagName: str) -> bool:
		scopeList = self.__scopeBaseList.copy()
		scopeList.append("button")
		return self.__hasInScopeImpl(tagName, scopeList)

	def hasInTableScope(self, tagName: str) -> bool:
		scopeList = ["html", "table", "template"]
		return self.__hasInScopeImpl(tagName, scopeList)

	def hasInListItemScope(self, tagName: str) -> bool:
		scopeList = self.__scopeBaseList.copy()
		scopeList.append("ol")
		scopeList.append("ul")
		return self.__hasInScopeImpl(tagName, scopeList)

	def hasInSelectScope(self, tagName: str) -> bool:
		scopeList = ["option", "optgroup"]
		return self.__hasInScopeImpl(tagName, scopeList)

	def contains(self, element: Element) -> bool:
		return element in self.__openElements

	def elements(self) -> List[Element]:
		return self.__openElements

	def popUntilElementWithAtagNameHasBeenPopped(self, tagName: str) -> None:
		while (len(self.__openElements) > 0):
			if (self.currentNode().name == tagName):
				self.pop()
				break
			else:
				self.pop()

	def topmostSpecialNodeBelow(self, formattingElement: Element) -> Union[Element, None]:
		foundElement: Union[Element, None] = None
		for element in reversed(self.elements()):
			if (element == formattingElement):
				break
			if (ParserUtils.isSpecialtag(element.name) and element.namespace):
				foundElement = element
		return foundElement

	def lastElementWithTagName(self, tagName: str) -> Union[LastElementResult, None]:
		for index, element in reversed(list(enumerate(self.elements()))):
			if (element.name == tagName):
				result = self.LastElementResult()
				result.index = index
				result.element = element
				return result

	def elementBefore(self, targetElement: Element) -> Union[Element, None]:
		foundTarget = False
		for element in reversed(self.__openElements):
			if (element == targetElement):
				foundTarget = True
			elif foundTarget:
				return element
		
		return None