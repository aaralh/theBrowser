from typing import List, Union
from web.dom.Document import Document


class Node:

    def __init__(self, parent: Union['Node', None], document: Document):
        self._parentNode: Union[Node, None] = parent
        self._childNodes: List[Node] = []
        self._nodeName: Union[str, None] = None
        self._document: Union[Document, None] = document

    def __str__(self):
        treeString = "*Document*\n"

        for node in self.childNodes:
            treeString += node.__str__()

        return treeString

    @property
    def name(self) -> Union[str, None]:
        return self._nodeName

    @name.setter
    def name(self, newName: str) -> None:
        self._nodeName = newName

    @property
    def parentNode(self) -> Union['Node', None]:
        return self._parentNode

    @parentNode.setter
    def parentNode(self, parent: 'Node') -> None:
        self._parentNode = parent

    def appendChild(self, node: 'Node') -> None:
        self._childNodes.append(node)

    def appendChildBeforeElement(self, node: 'Node', insertBefore: 'Node') -> None:
        index = self._childNodes.index(insertBefore)
        self._childNodes.insert(index, node)

    def removeChild(self, node: 'Node') -> None:
        self._childNodes.remove(node)

    @property
    def childNodes(self):
        return self._childNodes

    @property
    def document(self) -> Union[Document, None]:
        return self._document

    @document.setter
    def document(self, document: Document) -> None:
        self._document = document
