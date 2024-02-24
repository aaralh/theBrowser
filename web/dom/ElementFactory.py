from typing import Callable, Union, cast
from web.dom.Node import Node
from web.html.parser.HTMLToken import HTMLTag
from web.dom.elements.Element import Element
from web.dom.Document import Document
from web.dom.TagNames import TAG_NAMES
import re


def is_valid_html_name(name: str) -> bool:
    """
    Returns True if the given name is a valid name for a custom HTML element.
    """
    # A valid name must start with a letter and can be followed by any number of letters, digits, hyphens, or underscores.
    return bool(re.match(r"^[a-zA-Z][\w-]*$", name))


class ElementFactory:

    # self, token: HTMLTag, parent: Node, document: Document

    @staticmethod
    def create_element(token: HTMLTag, parent: Node, document: Document) -> Union[Element, None]:
        name = token.name
        if not name:
            return None
        lowerTagName = name.lower()
        constructor = cast(Callable[[HTMLTag, Node, Document], Element], TAG_NAMES.get(lowerTagName, None))

        if constructor is not None:
            return constructor(token, parent, document)
        else:
            # Handle custom elements
            illegal_custom_names = ["annotation-xml", "color-profile", "font-face", "font-face-src", "font-face-uri", "font-face-format", "font-face-name", "missing-glyph"]
            if name in illegal_custom_names or not is_valid_html_name(name):
                return None

            return Element(token, parent, document)
