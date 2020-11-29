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
		siblings = self.parentNode.childNodes
		textSiblingsData = [sibling.data for sibling in siblings if (type(sibling) is Text)]
		return "".join(textSiblingsData)