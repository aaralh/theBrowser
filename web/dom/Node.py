from typing import List, Union


class Node:

	def __init__(self):
		self.__parentNode: Union[Node, None] = None
		self.__childNodes: List[Node] = []
		self.__nodeName: Union[str, None] = None


	@property
	def name(self) -> Union[str, None]:
		return self.__nodeName
	
	@name.setter
	def name(self, newName: str) -> None:
		self.__nodeName = newName


	@property
	def parentNode(self) -> Union[Node, None]:
		return self.__parentNode
	
	@parentNode.setter
	def name(self, parent: Node) -> None:
		self.__parentNode = parent


	def appendChild(self, node: Node) -> None:
		self.__childNodes.append(node)
	

	def removeChild(self, node: Node) -> None:
		self.__childNodes.remove(node)
