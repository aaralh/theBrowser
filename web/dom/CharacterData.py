from web.dom.Document import Document
from web.dom.Node import Node
from web.html.parser.utils import charIsWhitespace


class CharacterData(Node):

    def __init__(self, data: str, parent: Node, document: Document):
        super(CharacterData, self).__init__(parent, document)
        self.__data = data
        self.length = len(data)

    def __str__(self) -> str:
        return f"<TEXT>{self.__data}</TEXT>"

    def __updateLength(self) -> None:
        self.length = len(self.__data)

    @property
    def data(self) -> str:
        return self.__data

    def substringData(self, offset: int, count: int) -> str:
        lastIndex = offset + count
        return self.__data[offset:lastIndex]

    def appendData(self, data: str) -> None:
        self.__data += data
        self.__updateLength()

    def insertData(self, offset: int, data: str) -> None:
        self.__updateLength()
        pass

    def deleteData(self, offset: int, count: int) -> None:
        self.__updateLength()
        pass

    def replaceData(self, offset: int, count: int, data: str) -> None:
        if offset > self.length:
            # TODO:Implement error
            pass
        elif offset + count > self.length:
            count = self.length - offset
        self.__updateLength()
        # TODO: Continue here
        pass

    def printTree(self, depth: int) -> str:
        indentation = ""

        for _ in range(depth):
            indentation += "\t"
        if not self.__data.isspace():
            return f"{indentation}" + f"<TEXT>{self.__data}</TEXT>" + "\n"
        else:
            return ""

    def get_contents(self) -> str:
        if not self.__data.isspace():
            return f"<TEXT>{self.__data.strip()}</TEXT>" + "\n"
        else:
            return ""
