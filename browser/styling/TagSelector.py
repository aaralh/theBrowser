from typing import List
from web.dom.elements.Element import Element
from utils import log

class TagSelector:
    def __init__(self, tag: str, classes: List[str], ids: list[str]):
        self.tag = tag
        self.priority = 1
        self.classes = classes
        self.ids = ids

    def check_match_for_tag_plus_class(self, node_name: str, classes: List[str]) -> bool:
        for cls in classes:
            if node_name + "." + cls == self.tag: return True
        return False

    def check_match_for_tag_plus_id(self, node_name: str, id: str) -> bool:
        if self.tag:
            return self.tag == node_name and "#"+id in self.ids
        else:
            return "#"+id in self.ids

    def matches(self, node: Element) -> bool:
        if not isinstance(node, Element): return False
        classes = [cls.lower() for cls in node.attributes.get("class", "").split(" ")]
        id = node.attributes.get("id", None)
        """ if node.name == "body":
            log("Matches:", self.tag, self.classes, node.name, node.attributes, (self.tag == node.name or (any(cls in self.classes for cls in classes))))
            log(self.classes, classes) """
        return  (
            self.tag == node.name or
            (any(cls in self.classes for cls in classes)) or
            ((self.tag and not self.tag.startswith(".") and self.tag.count(".") == 1) and self.check_match_for_tag_plus_class(node.name, classes)) or
         (id and self.check_match_for_tag_plus_id(node.name, id)))

    def __str__(self) -> str:
        return f"Tag: {self.tag}, class: {self.classes}, ids: {self.ids}"
