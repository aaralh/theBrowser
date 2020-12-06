from typing import List, Union
from web.dom.Document import Document

class Node:

	def __init__(self, parent: Union['Node', None], document: Document):
		self.__parentNode: Union[Node, None] = parent
		self.__childNodes: List[Node] = []
		self.__nodeName: Union[str, None] = None
		self.__document: Union[Document, None] = document

	def __str__(self):
		return f"""<{self.name}>
			{self.childNodes}"""


	@property
	def name(self) -> Union[str, None]:
		return self.__nodeName
	
	@name.setter
	def name(self, newName: str) -> None:
		self.__nodeName = newName

	@property
	def parentNode(self) -> Union['Node', None]:
		return self.__parentNode
	
	@parentNode.setter
	def parentNode(self, parent: 'Node') -> None:
		self.__parentNode = parent


	def appendChild(self, node: 'Node') -> None:
		self.__childNodes.append(node)
	

	def removeChild(self, node: 'Node') -> None:
		self.__childNodes.remove(node)

	@property
	def childNodes(self):
		return self.__childNodes

	@property
	def document(self) -> Union[Document, None]:
		return self.__document
	
	@document.setter
	def document(self, document: Document) -> None:
		self.__document = document