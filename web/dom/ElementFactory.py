from typing import Union
from web.dom.elements.Element import Element
from web.dom.Document import Document
from web.dom.TagNames import TAG_NAMES

class ElementFactory:

	@staticmethod
	def create_element(document: Document, token: str) -> Union[Element, None]:
		lowerTagName = tagName.lower()
		constructor = TAG_NAMES.get(lowerTagName, None)

		if (constructor is not None):
			return constructor()
		

