from web.dom.Node import Node
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from web.dom.Document import Document
	from web.html.parser.HTMLToken import HTMLDoctype


class DocumentType(Node):
	def __init__(self, documentToken: 'HTMLDoctype', document: 'Document'):
		super(DocumentType, self).__init__(None, document)
		self.name: str = documentToken.name if documentToken.name != None else ""
		self.__publicId: str = documentToken.publicIdentifier if documentToken.publicIdentifier != None else ""
		self.__systemId: str = documentToken.systemPublicIdentidier if documentToken.systemPublicIdentidier != None else ""
		self.__forcedQuircks: bool = False