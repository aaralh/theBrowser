from typing import List
from web.dom.elements.Element import Element

class TagSelector:
    def __init__(self, tag: str, classes: List[str]):
        self.tag = tag
        self.priority = 1
        self.classes = classes

    def matches(self, node: Element) -> bool:
        if not isinstance(node, Element): return False
        classes = [cls.lower() for cls in node.attributes.get("class", "").split(" ")]
        return  (self.tag == node.name or (self.tag.startswith(".") and self.tag[1:] in classes))
