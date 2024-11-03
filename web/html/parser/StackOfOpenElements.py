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
        self.__open_elements: List[Element] = []
        self.__scope_base_list: List[str] = ["applet", "caption", "html", "table", "td", "th", "marquee", "object",
                                           "template"]

    def __has_in_scope_impl(self, target_node_name: str, tag_name_list: List[str]) -> bool:
        for node in reversed(self.__open_elements):
            if node.name == target_node_name:
                return True
            if node.name in tag_name_list:
                return False
        return False

    def pop_all_elements(self) -> None:
        while not self.is_empty():
            self.__open_elements.pop()

    def is_empty(self) -> bool:
        return len(self.__open_elements) == 0

    def first(self) -> Optional[Element]:
        if not self.is_empty():
            return self.__open_elements[0]
        return None

    def last(self) -> Optional[Element]:
        if not self.is_empty():
            return self.__open_elements[-1]
        return None

    def push(self, element: Element) -> None:
        self.__open_elements.append(element)

    def pop(self) -> Optional[Element]:
        if not self.is_empty():
            return self.__open_elements.pop()
        return None

    def current_node(self) -> Optional[Element]:
        return self.last()

    def has_in_scope(self, tag_name: str) -> bool:
        return self.__has_in_scope_impl(tag_name, self.__scope_base_list)

    def has_in_button_scope(self, tag_name: str) -> bool:
        scope_list = self.__scope_base_list.copy()
        scope_list.append("button")
        return self.__has_in_scope_impl(tag_name, scope_list)

    def has_in_table_scope(self, tag_name: str) -> bool:
        scope_list = ["html", "table", "template"]
        return self.__has_in_scope_impl(tag_name, scope_list)

    def has_in_list_item_scope(self, tag_name: str) -> bool:
        scope_list = self.__scope_base_list.copy()
        scope_list.append("ol")
        scope_list.append("ul")
        return self.__has_in_scope_impl(tag_name, scope_list)

    def has_in_select_scope(self, tag_name: str) -> bool:
        scope_list = ["option", "optgroup"]
        return self.__has_in_scope_impl(tag_name, scope_list)

    def contains(self, element_name: str) -> bool:
        for element in self.__open_elements:
            if element.name == element_name:
                return True

        return False

    def contains_element(self, element: Element) -> bool:
        return element in self.__open_elements

    def elements(self) -> List[Element]:
        return self.__open_elements

    def pop_until_element_with_tag_name_has_been_popped(self, tag_name: str) -> None:
        while len(self.__open_elements) > 0:
            currentNode = self.current_node()
            if currentNode is not None:
                if currentNode.name == tag_name:
                    self.pop()
                    break
                else:
                    self.pop()

    def topmost_special_node_below(self, formatting_element: Element) -> Optional[Result]:
        result: Optional[StackOfOpenElements.Result] = None
        for index, element in reversed(list(enumerate(self.elements()))):
            if element == formatting_element:
                break
            if ParserUtils.isSpecialtag(element.name) and element.namespace:
                result = self.Result(index, element)
        return result

    def last_element_with_tag_name(self, tag_name: str) -> Optional[Result]:
        for index, element in reversed(list(enumerate(self.elements()))):
            if element.name == tag_name:
                result = self.Result()
                result.index = index
                result.element = element
                return result
        return None

    def element_before(self, target_element: Element) -> Optional[Element]:
        found_target = False
        for element in reversed(self.__open_elements):
            if element == target_element:
                found_target = True
            elif found_target:
                return element

        return None

    def get_element_on_index(self, index: int) -> Optional[Element]:
        if len(self.__open_elements) < index:
            return None
        else:
            return self.__open_elements[index]
