from typing import List
from web.dom.elements.Element import Element

class TagSelector:
    def __init__(self, tag: str, classes: List[str], ids: str):
        self.tag = tag
        self.priority = 1
        self.classes = classes
        self.ids = ids

    def check_match_for_tag_plus_class(self, node_name: str, classes: List[str]) -> bool:
        for cls in classes:
            if node_name + "." + cls == self.tag: return True
        return False

    def matches(self, node: Element) -> bool:
        if not isinstance(node, Element): return False
        classes = [cls.lower() for cls in node.attributes.get("class", "").split(" ")]
        id = node.attributes.get("id", None)
        """ if node.name == "body":
            print("Matches:", self.tag, self.classes, node.name, node.attributes, (self.tag == node.name or (any(cls in self.classes for cls in classes))))
            print(self.classes, classes) """
        return  (self.tag == node.name or 
        (any(cls in self.classes for cls in classes)) or 
        ((self.tag and not self.tag.startswith(".") and self.tag.count(".") == 1) and self.check_match_for_tag_plus_class(node.name, classes)) or 
         (id and "#"+id in self.ids))

    def __str__(self) -> str:
        return f"Tag: {self.tag}, class: {self.classes}"