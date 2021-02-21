from dataclasses import dataclass
from typing import List, Union

from web.dom.elements.Element import Element
from web.html.parser.ParserUtils import ParserUtils


class StackOfOpenElments:
    @dataclass
    class Result:
        index: Union[int, None] = None
        element: Union[Element, None] = None

    def __init__(self):
        self._openElements: List[Element] = []
        self._scopeBaseList: List[str] = ["applet", "caption", "html", "table", "td", "th", "marquee", "object",
                                          "template"]

    def _hasInScopeImpl(self, targetNodeName: str, tagNameList: List[str]) -> bool:
        for node in reversed(self._openElements):
            if node.name == targetNodeName:
                return True
            if node.name in tagNameList:
                return False

    def popAllElements(self) -> None:
        while not self.isEmpty():
            self._openElements.pop()

    def isEmpty(self) -> bool:
        return len(self._openElements) == 0

    def first(self) -> Union[Element, None]:
        if not self.isEmpty():
            return self._openElements[0]
        return None

    def last(self) -> Union[Element, None]:
        if not self.isEmpty():
            return self._openElements[-1]
        return None

    def push(self, element: Element) -> None:
        self._openElements.append(element)

    def pop(self) -> Union[Element, None]:
        if not self.isEmpty():
            return self._openElements.pop()
        return None

    def currentNode(self) -> Union[Element, None]:
        return self.last()

    def hasInScope(self, tagName: str) -> bool:
        return self._hasInScopeImpl(tagName, self._scopeBaseList)

    def hasInButtonScope(self, tagName: str) -> bool:
        scopeList = self._scopeBaseList.copy()
        scopeList.append("button")
        return self._hasInScopeImpl(tagName, scopeList)

    def hasInTableScope(self, tagName: str) -> bool:
        scopeList = ["html", "table", "template"]
        return self._hasInScopeImpl(tagName, scopeList)

    def hasInListItemScope(self, tagName: str) -> bool:
        scopeList = self._scopeBaseList.copy()
        scopeList.append("ol")
        scopeList.append("ul")
        return self._hasInScopeImpl(tagName, scopeList)

    def hasInSelectScope(self, tagName: str) -> bool:
        scopeList = ["option", "optgroup"]
        return self._hasInScopeImpl(tagName, scopeList)

    def contains(self, elementName: str) -> bool:
        for element in self._openElements:
            if element.name == elementName:
                return True

        return False

    def containsElement(self, element: Element) -> bool:
        return element in self._openElements

    def elements(self) -> List[Element]:
        return self._openElements

    def popUntilElementWithAtagNameHasBeenPopped(self, tagName: str) -> None:
        while len(self._openElements) > 0:
            print("Current:", self.currentNode().name)
            print("TagName: ", tagName)
            if self.currentNode().name == tagName:
                self.pop()
                break
            else:
                self.pop()

    def topmostSpecialNodeBelow(self, formattingElement: Element) -> Union[Result, None]:
        result: Union[self.Result, None] = None
        for index, element in reversed(list(enumerate(self.elements()))):
            if element == formattingElement:
                break
            if ParserUtils.isSpecialtag(element.name) and element.namespace:
                result = self.Result(index, element)
        return result

    def lastElementWithTagName(self, tagName: str) -> Union[Result, None]:
        for index, element in reversed(list(enumerate(self.elements()))):
            if element.name == tagName:
                result = self.Result()
                result.index = index
                result.element = element
                return result

    def elementBefore(self, targetElement: Element) -> Union[Element, None]:
        foundTarget = False
        for element in reversed(self._openElements):
            if element == targetElement:
                foundTarget = True
            elif foundTarget:
                return element

        return None

    def getElementOnIndex(self, index: int) -> Union[Element, None]:
        if len(self._openElements) < index:
            return None
        else:
            return self._openElements[index]
