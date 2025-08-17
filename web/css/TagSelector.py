from typing import List
from web.dom.elements.Element import Element

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
        matches = []

        
        if len(self.tag) > 0 and "." in self.tag:
            matches.append(self.check_match_for_tag_plus_class(node.name, classes))
        elif len(self.tag) > 0:
            matches.append(self.tag == node.name)

        if len(self.classes) > 0:
            matches.append(any(cls in self.classes for cls in classes))
        if len(self.ids) > 0:
            matches.append(id and self.check_match_for_tag_plus_id(node.name, id))

        return all(matches)

    def __str__(self) -> str:
        return f"Tag: {self.tag}, class: {self.classes}, ids: {self.ids}"
