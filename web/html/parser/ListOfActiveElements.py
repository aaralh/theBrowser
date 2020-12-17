from typing import List, Union
from web.dom.elements.Element import Element
from web.dom.Node import Node
from dataclasses import dataclass

class ListOfActiveElements:

	@dataclass
	class Entry:
		element: Node
		
		@property
		def isMarker(self) -> bool:
			return self.element is None


	def __init__(self):
		self.__listOfActiveElements: List[self.Entry] = []
	

	def isEmpty(self) -> bool:
		return len(self.__listOfActiveElements) == 0

	def contains(self, element: Node) -> bool:
		for item in self.__listOfActiveElements:
			if item.element == element:
				return True
		
		return False
	
	def push(self, element: Node) -> None:
		self.__listOfActiveElements.append(self.Entry(element))

	def lastEntry(self) -> Union[Entry, None]:
		if (self.isEmpty()):
			return None
		return self.__listOfActiveElements[-1]

	def addMarker(self) -> None:
		self.__listOfActiveElements.append(self.Entry(None))


	def remove(self, element: Node) -> None:
		entries = List[filter(lambda entry: entry.element == element,  self.__listOfActiveElements)]
		if len(entries) > 0:
			self.__listOfActiveElements.remove(entries[0])

	def entries(self) -> List['Entry']:
		return self.__listOfActiveElements

	def lastElementWithTagNameBeforeMarker(self, tagName: str) -> Union[Node, None]:
		for entry in reversed(self.__listOfActiveElements):
			if (entry.isMarker):
				return None
			if (entry.element.name == tagName):
				return entry.element
		
		return None
			


	def clearUpToTheLastMarker(self) -> None:
		while (not self.isEmpty()):
			entry = self.__listOfActiveElements[-1]
			if (entry.isMarker()):
				break
			else:
				self.__listOfActiveElements.remove(entry)