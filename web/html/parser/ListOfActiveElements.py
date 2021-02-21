from typing import List, Union
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
        index: Union[int, None] = None
        element: Union[Element, None] = None

    def __init__(self):
        self._listOfActiveElements: List[self.Entry] = []

    def isEmpty(self) -> bool:
        return len(self._listOfActiveElements) == 0

    def contains(self, element: Element) -> bool:
        for item in self._listOfActiveElements:
            if item.element == element:
                return True

        return False

    def push(self, element: Element) -> None:
        self._listOfActiveElements.append(self.Entry(element))

    def lastEntry(self) -> Union[Entry, None]:
        if self.isEmpty():
            return None
        return self._listOfActiveElements[-1]

    def addMarker(self) -> None:
        self._listOfActiveElements.append(self.Entry(None))

    def remove(self, element: Element) -> None:
        entries = List[filter(lambda entry: entry.element == element, self._listOfActiveElements)]
        if len(entries) > 0:
            self._listOfActiveElements.remove(entries[0])

    def entries(self) -> List['Entry']:
        return self._listOfActiveElements

    def lastElementWithTagNameBeforeMarker(self, tagName: str) -> Union[Result, None]:
        for index, entry in reversed(list(enumerate(self._listOfActiveElements))):
            if entry.isMarker:
                return None
            if entry.element.name == tagName:
                return self.Result(index, entry.element)

        return None

    def clearUpToTheLastMarker(self) -> None:
        while not self.isEmpty():
            entry = self._listOfActiveElements[-1]
            if entry.isMarker:
                break
            else:
                self._listOfActiveElements.remove(entry)
