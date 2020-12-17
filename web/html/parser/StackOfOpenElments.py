
from typing import List, Union

from web.dom.Node import Node


class StackOfOpenElments:

	def __init__(self):
		self.__openElements: List[Node] = []

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
		for element in self.__openElements:
			if (element.name == tagName):
				return True
		return False

	def hasInButtonScope(self, tagName: str) -> bool:
		pass

	def hasInTableScope(self, tagName: str) -> bool:
		pass

	def hasInListItemScope(self, tagName: str) -> bool:
		pass

	def hasInSelectScope(self, tagName: str) -> bool:
		pass

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
		pass

	def lastElementWithTagName(self, tagName: str) -> Union[Node, None]:
		for element in reversed(self.elements()):
			if (element.name == tagName):
				return element

	def elementBefore(self, element: Node) -> Union[Node, None]:
		pass