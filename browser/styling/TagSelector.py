from typing import List
from web.dom.elements.Element import Element

class TagSelector:
    def __init__(self, tag: str, classes: List[str]):
        self.tag = tag
        self.priority = 1
        self.classes = classes

    def check_match_for_tag_plus_class(self, node_name: str, classes: List[str]) -> bool:
        for cls in classes:
            if node_name + "." + cls == self.tag: return True
        return False

    def matches(self, node: Element) -> bool:
        if not isinstance(node, Element): return False
        classes = [cls.lower() for cls in node.attributes.get("class", "").split(" ")]
        #print("Matches:", self.tag, node.name, (self.tag == node.name or (self.tag.startswith(".") and self.tag[1:] in classes)))
        return  (self.tag == node.name or 
        (self.tag.startswith(".") and self.tag[1:] in classes) or 
        ((not self.tag.startswith(".") and self.tag.count(".") == 1) and self.check_match_for_tag_plus_class(node.name, classes)))
