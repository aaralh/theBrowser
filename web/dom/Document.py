from typing import Union
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from web.dom.elements.Element import Element


class Document:
    def __init__(self):
        self._head: Union['Element', None] = None
        self._forms: Union['Element', None] = None
        self._title: Union[str, None] = None

    @property
    def head(self) -> Union['Element', None]:
        return self._head

    @head.setter
    def head(self, node: 'Element') -> None:
        self._head = node

    @property
    def title(self) -> Union['Element', None]:
        return self._title

    @title.setter
    def title(self, title: str) -> None:
        self._title = title

    @property
    def forms(self) -> Union['Element', None]:
        return self._forms
