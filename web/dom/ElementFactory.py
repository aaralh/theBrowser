from typing import Callable, Union, cast
from web.dom.Node import Node
from web.html.parser.HTMLToken import HTMLTag
from web.dom.elements.Element import Element
from web.dom.Document import Document
from web.dom.TagNames import TAG_NAMES


class ElementFactory:

    # self, token: HTMLTag, parent: Node, document: Document

    @staticmethod
    def create_element(token: HTMLTag, parent: Node, document: Document) -> Union[Element, None]:
        lowerTagName = token.name.lower()
        constructor = cast(Callable[[HTMLTag, Node, Document], Element], TAG_NAMES.get(lowerTagName, None))

        if constructor is not None:
            return constructor(token, parent, document)
