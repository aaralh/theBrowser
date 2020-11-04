from typing import Union
from web.dom.Node import Node


class CharacterData(Node):
	def __init__(self, data: Union[str, None]):
		self.__data: str = data if data != None else ""

class Comment(CharacterData):
	pass