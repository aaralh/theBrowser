from web.html.parser.HTMLToken import HTMLDoctype
from web.dom.Node import Node


class DocumentType(Node):
	def __init__(self, documentToken: HTMLDoctype):
		self.name: str = documentToken.name if documentToken.name != None else ""
		self.__publicId: str = documentToken.publicIdentifier if documentToken.publicIdentifier != None else ""
		self.__systemId: str = documentToken.systemPublicIdentidier if documentToken.systemPublicIdentidier != None else ""
		self.__forcedQuircks: bool = False