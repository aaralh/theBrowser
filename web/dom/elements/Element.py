from typing import Dict, Union
from web.dom.Document import Document
from web.html.parser.HTMLToken import HTMLCommentOrCharacter, HTMLDoctype, HTMLTag, HTMLToken
from web.dom.Node import Node


class Element(Node):
    def __init__(self, token: HTMLTag, parent: Node, document: Document, namespace: str = ""):
        super(Element, self).__init__(parent, document)
        self._localName = token.name
        self._is = token.attributes.get("id", None)
        self._attributes = token.attributes
        self._namespace: str = namespace

    def __str__(self):
        return self.printTree()

    def printTree(self, depth: int = 0) -> str:
        indentation = ""
        for _ in range(depth):
            indentation += "\t"
        depth += 1
        treeString = f"{indentation}<{self.name} {self.attributes}>"
        for node in self.childNodes:
            treeString += "\n"
            treeString += node.printTree(depth)

        if self.childNodes:
            treeString += f"{indentation}</{self.name}>\n"
        else:
            treeString += f"</{self.name}>\n"

        return treeString

    @property
    def namespace(self) -> str:
        return self._namespace

    @property
    def name(self) -> str:
        return self._localName

    @property
    def attributes(self) -> Dict[str, str]:
        return self._attributes
