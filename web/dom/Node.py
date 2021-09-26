from typing import List, Union
from web.dom.Document import Document
from web.dom.events.EventTarget import EventTarget


class Node(EventTarget):

    def __init__(self, parent: Union['Node', None], document: Document):
        self.__parentNode: Union[Node, None] = parent
        self.__children: List[Node] = []
        self.__nodeName: Union[str, None] = None
        self.__document: Union[Document, None] = document

    def __str__(self) -> str:
        treeString = "*Document*\n"

        for node in self.children:
            treeString += node.__str__()

        return treeString

    @property
    def name(self) -> Union[str, None]:
        return self.__nodeName

    @name.setter
    def name(self, newName: str) -> None:
        self.__nodeName = newName

    @property
    def parentNode(self) -> Union['Node', None]:
        return self.__parentNode

    @parentNode.setter
    def parentNode(self, parent: 'Node') -> None:
        self.__parentNode = parent

    def appendChild(self, node: 'Node') -> None:
        self.__children.append(node)

    def appendChildBeforeElement(self, node: 'Node', insertBefore: 'Node') -> None:
        index = self.__children.index(insertBefore)
        self.__children.insert(index, node)

    def removeChild(self, node: 'Node') -> None:
        self.__children.remove(node)

    @property
    def children(self) -> List['Node']:
        return self.__children

    @property
    def document(self) -> Union[Document, None]:
        return self.__document

    @document.setter
    def document(self, document: Document) -> None:
        self.__document = document
