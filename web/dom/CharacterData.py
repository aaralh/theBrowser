from web.dom.exceptions.DomException import DomException
from web.dom.Node import Node

class CharacterData(Node):
	
	def __init__(self, data: str):
		self.data = data
		self.length = len(data)
	
	def _updateLength(self) -> None:
		self.length = len(self.data)

	def substringData(self, offset: int, count: int) -> str:
		lastIndex = offset + count
		return self.data[offset:lastIndex]

	def appendData(self, data: str) -> None:
		self.data + data
		self._updateLength()

	def insertData(self, offset: int, data: str) -> None:
		self._updateLength()
		pass

	def deleteData(self, offset: int, count: int) -> None:
		self._updateLength()
		pass

	def replaceData(self, offset: int, count: int, data: str) -> None:
		if (offset > self.length):
			raise DomException("", "IndexSizeError")
		elif (offset + count > self.length):
			count = self.length - offset
		self._updateLength()
		# TODO: Continue here
		pass
