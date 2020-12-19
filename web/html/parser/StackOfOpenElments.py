
from typing import List, Union

from web.dom.Node import Node


class StackOfOpenElments:

	def __init__(self):
		self.__openElements: List[Node] = []
		self.__scopeBaseList: List[str] = ["applet", "caption", "html", "table", "td", "th", "marquee", "object", "template"]

	def __hasInScopeImpl(self, targetNodeName: str, tagNameList: List[str]) -> bool:
		for node in reversed(self.__openElements):
			if (node.name == targetNodeName):
				return True
			if (node.name in tagNameList):
				return False



	def isEmpty(self) -> bool:
		return len(self.__openElements) == 0

	def first(self) -> Union[Node, None]:
		if (not self.isEmpty()):
			return self.__openElements[0]
		return None

	def last(self) -> Union[Node, None]:
		if (not self.isEmpty()):
			return self.__openElements[-1]
		return None

	def push(self, element: Node) -> None:
		self.__openElements.append(element)

	def pop(self) -> Union[Node, None]:
		if (not self.isEmpty()):
			return self.__openElements.pop()
		return None

	def currentNode(self) -> Union[Node, None]:
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

	def contains(self, element: Node) -> bool:
		return element in self.__openElements

	def elements(self) -> List[Node]:
		return self.__openElements

	def popUntilElementWithAtagNameHasBeenPopped(self, tagName: str) -> None:
		while (len(self.__openElements) > 0):
			if (self.currentNode().name == tagName):
				self.pop()
				return
			else:
				self.pop()

	def topmostSpecialNodeBelow(self, element: Node) -> Union[Node, None]:
		raise NotImplementedError

	def lastElementWithTagName(self, tagName: str) -> Union[Node, None]:
		for element in reversed(self.elements()):
			if (element.name == tagName):
				return element

	def elementBefore(self, targetNode: Node) -> Union[Node, None]:
		foundTarget = False
		for element in reversed(self.__openElements):
			if (element == targetNode):
				foundTarget = True
			elif foundTarget:
				return element
		
		return None