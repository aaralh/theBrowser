from typing import Dict, Union, Optional
from web.dom.Document import Document
from web.html.parser.HTMLToken import HTMLCommentOrCharacter, HTMLDoctype, HTMLTag, HTMLToken
from web.dom.Node import Node


class Element(Node):
    def __init__(self, token: HTMLTag, parent: Node, document: Document, namespace: str = "") -> None:
        super(Element, self).__init__(parent, document)
        self.__localName: Optional[str] = token.name
        self.__id = token.attributes.get("id", None)
        self.__attributes: Dict[str, str] = token.attributes
        self.__namespace: str = namespace
        self.style: Optional[Dict] = None

    def __str__(self) -> str:
        return self.printTree()

    def to_string(self) -> str:
        return self.get_contents()

    def get_contents(self) -> str:

        treeString = f"<{self.name} {self.attributes}>"
        for node in self.children:
            treeString += node.get_contents()

        if self.children:
            treeString += f"</{self.name}>"
        else:
            treeString += f"</{self.name}>"

        return treeString

    def printTree(self, depth: int = 0) -> str:
        indentation = ""
        for _ in range(depth):
            indentation += "\t"
        depth += 1
        treeString = f"{indentation}<{self.name} {self.attributes}>"
        for node in self.children:
            treeString += "\n"
            treeString += node.printTree(depth)

        if self.children:
            treeString += f"{indentation}</{self.name}>\n"
        else:
            treeString += f"</{self.name}>\n"

        return treeString

    @property
    def namespace(self) -> str:
        return self.__namespace

    @property
    def name(self) -> Optional[str]:
        return self.__localName

    @property
    def attributes(self) -> Dict[str, str]:
        return self.__attributes
