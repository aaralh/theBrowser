from typing import List, Optional, cast
from web.dom.elements.Element import Element
from dataclasses import dataclass


class ListOfActiveElements:
    @dataclass
    class Entry:
        element: Element

        @property
        def isMarker(self) -> bool:
            return self.element is None

    @dataclass
    class Result:
        index: Optional[int] = None
        element: Optional[Element] = None

    def __init__(self) -> None:
        self.__listOfActiveElements: List[ListOfActiveElements.Entry] = []

    def isEmpty(self) -> bool:
        return len(self.__listOfActiveElements) == 0

    def contains(self, element: Element) -> bool:
        for item in self.__listOfActiveElements:
            if item.element == element:
                return True

        return False

    def push(self, element: Element) -> None:
        self.__listOfActiveElements.append(self.Entry(element))

    def lastEntry(self) -> Optional[Entry]:
        if self.isEmpty():
            return None
        return self.__listOfActiveElements[-1]

    def addMarker(self) -> None:
        self.__listOfActiveElements.append(self.Entry(None))

    def remove(self, element: Element) -> None:
        entries = filter(lambda entry: entry.element == element, self.__listOfActiveElements)
        entries_list = list(entries)
        if len(entries_list) > 0:
            self.__listOfActiveElements.remove(entries_list[0])

    def entries(self) -> List[Entry]:
        return self.__listOfActiveElements

    def lastElementWithTagNameBeforeMarker(self, tagName: str) -> Optional[Result]:
        for index, entry in reversed(list(enumerate(self.__listOfActiveElements))):
            if entry.isMarker:
                return None
            if entry.element.name == tagName:
                return self.Result(index, entry.element)

        return None

    def clearUpToTheLastMarker(self) -> None:
        while not self.isEmpty():
            entry = self.__listOfActiveElements[-1]
            if entry.isMarker:
                break
            else:
                self.__listOfActiveElements.remove(entry)

    def entryBefore(self, entry: Entry) -> Optional[Entry]:
        index = self.__listOfActiveElements.index(entry)
        if index == 0:
            return  None
        return self.__listOfActiveElements[index - 1]

    def entryAfter(self, entry: Entry) -> Optional[Entry]:
        index = self.__listOfActiveElements.index(entry)
        if index == len(self.__listOfActiveElements) - 1:
            return  None
        return self.__listOfActiveElements[index + 1]
