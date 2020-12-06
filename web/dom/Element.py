from typing import Union
from web.dom.Document import Document
from web.html.parser.HTMLToken import HTMLCommentOrCharacter, HTMLDoctype, HTMLTag, HTMLToken
from web.dom.Node import Node


class Element(Node):
	def __init__(self, token: HTMLTag, parent: Node, document: Document):
		super(Element, self).__init__(parent, document)
		self.__localName = token.name
		self.__is = token.attributes.get("id", None)
		self.__attributes = token.attributes
	""" 	self.__tagName
		self.__id
		self.__className
		self.__classList
		self.__slot """

	@property
	def name(self) -> str:
		return self.__localName