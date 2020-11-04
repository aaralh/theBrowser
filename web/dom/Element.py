from typing import Union
from web.html.parser.HTMLToken import HTMLCommentOrCharacter, HTMLDoctype, HTMLTag, HTMLToken
from web.dom.Node import Node


class Element(Node):
	def __init__(self, token: HTMLTag, parent: Node):
		self.__localName = token.name
		self.__is = token.attributes["id"] if (token.attributes["id"] != None) else ""
		self.__attributes = token.attributes
		self.parentNode = parent
	""" 	self.__tagName
		self.__id
		self.__className
		self.__classList
		self.__slot """