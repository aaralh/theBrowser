from web.dom.CharacterData import CharacterData

class Text(CharacterData):

	def __init__(self, data=""):
		super(data)

	def splitText(self, offset: int) -> 'Text':
		reminder = self.data[:offset]
		self.data = self.data[offset:]
		return Text(reminder)

	@property
	def wholeText(self) -> str:
		return self.data