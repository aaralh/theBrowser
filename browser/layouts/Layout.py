from typing import List, Literal
from web.dom.Node import Node
from web.dom.elements.Text import Text
from web.dom.elements.Element import Element

BLOCK_ELEMENTS = [
    "html", "body", "article", "section", "nav", "aside",
    "h1", "h2", "h3", "h4", "h5", "h6", "hgroup", "header",
    "footer", "address", "p", "hr", "pre", "blockquote",
    "ol", "ul", "menu", "li", "dl", "dt", "dd", "figure",
    "figcaption", "main", "div", "table", "form", "fieldset",
    "legend", "details", "summary"
]

class Layout:

    node: Element
    parent: 'Layout'
    children: List['Layout']

    x: int
    y: int
    width: int
    height: int

    def __init__(self):
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        self.display_list = None

    def layout(self) -> None:
        raise NotImplementedError()

    def layout_mode(self, node: Node) -> Literal["inline", "block"]:
        if isinstance(node, Text):
            return "inline"
        elif node.childNodes:
            for child in node.childNodes:
                if isinstance(child, Text): continue
                if child.name in BLOCK_ELEMENTS:
                    return "block"
            return "inline"
        else:
            return "block"

    def paint(self) -> None:
        raise NotImplementedError()