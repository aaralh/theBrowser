from web.dom.Document import Document
from web.dom.Node import Node

class CharacterData(Node):
	
	def __init__(self, data: str, parent: Node, document: Document):
		super(CharacterData, self).__init__(parent, document)
		self.data = data
		self.length = len(data)
	
	def _updateLength(self) -> None:
		self.length = len(self.data)

	def substringData(self, offset: int, count: int) -> str:
		lastIndex = offset + count
		return self.data[offset:lastIndex]

	def appendData(self, data: str) -> None:
		self.data += data
		self._updateLength()

	def insertData(self, offset: int, data: str) -> None:
		self._updateLength()
		pass

	def deleteData(self, offset: int, count: int) -> None:
		self._updateLength()
		pass

	def replaceData(self, offset: int, count: int, data: str) -> None:
		if (offset > self.length):
			#TODO:Implement error
			pass 
		elif (offset + count > self.length):
			count = self.length - offset
		self._updateLength()
		# TODO: Continue here
		pass

	def __str__(self) -> str:
		return self.data

	def printTree(self, depth: int) -> str:
		indentation = ""

		for _ in range(depth):
			indentation += "\t"

		return  f"{indentation}" + self.data + "\n"
