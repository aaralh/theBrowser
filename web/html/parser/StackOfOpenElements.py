from dataclasses import dataclass
from typing import List, Optional
from web.dom.elements.Element import Element
from web.html.parser.ParserUtils import ParserUtils


class StackOfOpenElements:

    @dataclass
    class Result:
        index: Optional[int] = None
        element: Optional[Element] = None

    def __init__(self) -> None:
        self.__openElements: List[Element] = []
        self.__scopeBaseList: List[str] = ["applet", "caption", "html", "table", "td", "th", "marquee", "object",
                                           "template"]

    def __hasInScopeImpl(self, targetNodeName: str, tagNameList: List[str]) -> bool:
        for node in reversed(self.__openElements):
            if node.name == targetNodeName:
                return True
            if node.name in tagNameList:
                return False
        return False

    def popAllElements(self) -> None:
        while not self.isEmpty():
            self.__openElements.pop()

    def isEmpty(self) -> bool:
        return len(self.__openElements) == 0

    def first(self) -> Optional[Element]:
        if not self.isEmpty():
            return self.__openElements[0]
        return None

    def last(self) -> Optional[Element]:
        if not self.isEmpty():
            return self.__openElements[-1]
        return None

    def push(self, element: Element) -> None:
        self.__openElements.append(element)

    def pop(self) -> Optional[Element]:
        if not self.isEmpty():
            return self.__openElements.pop()
        return None

    def currentNode(self) -> Optional[Element]:
        return self.last()

    def hasInScope(self, tagName: str) -> bool:
        return self.__hasInScopeImpl(tagName, self.__scopeBaseList)

    def hasInButtonScope(self, tagName: str) -> bool:
        scopeList = self.__scopeBaseList.copy()
        scopeList.append("button")
        return self.__hasInScopeImpl(tagName, scopeList)

    def hasInTableScope(self, tagName: str) -> bool:
        scopeList = ["html", "table", "template"]
        return self.__hasInScopeImpl(tagName, scopeList)

    def hasInListItemScope(self, tagName: str) -> bool:
        scopeList = self.__scopeBaseList.copy()
        scopeList.append("ol")
        scopeList.append("ul")
        return self.__hasInScopeImpl(tagName, scopeList)

    def hasInSelectScope(self, tagName: str) -> bool:
        scopeList = ["option", "optgroup"]
        return self.__hasInScopeImpl(tagName, scopeList)

    def contains(self, elementName: str) -> bool:
        for element in self.__openElements:
            if element.name == elementName:
                return True

        return False

    def containsElement(self, element: Element) -> bool:
        return element in self.__openElements

    def elements(self) -> List[Element]:
        return self.__openElements

    def popUntilElementWithAtagNameHasBeenPopped(self, tagName: str) -> None:
        while len(self.__openElements) > 0:
            currentNode = self.currentNode()
            if currentNode is not None:
                if currentNode.name == tagName:
                    self.pop()
                    break
                else:
                    self.pop()

    def topmostSpecialNodeBelow(self, formattingElement: Element) -> Optional[Result]:
        result: Optional[StackOfOpenElements.Result] = None
        for index, element in reversed(list(enumerate(self.elements()))):
            if element == formattingElement:
                break
            if ParserUtils.isSpecialtag(element.name) and element.namespace:
                result = self.Result(index, element)
        return result

    def lastElementWithTagName(self, tagName: str) -> Optional[Result]:
        for index, element in reversed(list(enumerate(self.elements()))):
            if element.name == tagName:
                result = self.Result()
                result.index = index
                result.element = element
                return result
        return None

    def elementBefore(self, targetElement: Element) -> Optional[Element]:
        foundTarget = False
        for element in reversed(self.__openElements):
            if element == targetElement:
                foundTarget = True
            elif foundTarget:
                return element

        return None

    def getElementOnIndex(self, index: int) -> Optional[Element]:
        if len(self.__openElements) < index:
            return None
        else:
            return self.__openElements[index]
