from web.dom.Node import Node

class CharacterData(Node):
	
	def __init__(self, data: str):
		self.data = data
	
	def substringData(offset: int, count: int) -> str:
		pass

	def appedData(self, data: str) -> None:
		self.data + data

	def insertData(offset: int, data: str) -> None:
		pass

	def deleteData(offset: int, count: int) -> None:
		pass

	def replaceData(offset: int, count: int, data: str) -> None:
		pass
