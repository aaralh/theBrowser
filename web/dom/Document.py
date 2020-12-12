
from typing import Union
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from web.dom.elements.HTMLElement import HTMLElement

class Document:
	def __init__(self):
		self.__head: Union['HTMLElement', None] = None
		self.__form: Union['HTMLElement', None] = None
		self.__title: Union[str, None] = None


	@property
	def head(self) -> Union['HTMLElement', None]:
		return self.__head

	@head.setter
	def head(self, node: 'HTMLElement') -> None:
		self.__head = node

	@property
	def title(self) -> Union['HTMLElement', None]:
		return self.__title

	@title.setter
	def title(self, title: str) -> None:
		self.__title = title