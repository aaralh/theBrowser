
from typing import Union
from web.dom.Node import Node


class Document(Node):
	def __init__(self):
		self.__head: Union[Node, None] = None
		self.__form: Union[Node, None] = None

	@property.getter
	def head(self) -> Union[Node, None]:
		return self.__head

	@property.setter
	def head(self, node: Node) -> None:
		self.__head = node