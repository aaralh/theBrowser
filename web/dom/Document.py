
from typing import Union
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from web.dom.elements.Element import Element

class Document:
	def __init__(self):
		self.__head: Union['Element', None] = None
		self.__forms: Union['Element', None] = None
		self.__title: Union[str, None] = None


	@property
	def head(self) -> Union['Element', None]:
		return self.__head

	@head.setter
	def head(self, node: 'Element') -> None:
		self.__head = node

	@property
	def title(self) -> Union['Element', None]:
		return self.__title

	@title.setter
	def title(self, title: str) -> None:
		self.__title = title
	
	@property
	def forms(self) -> Union['Element', None]:
		return self.__forms