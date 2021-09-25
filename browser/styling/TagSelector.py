from web.dom.elements.Element import Element

class TagSelector:
    def __init__(self, tag: str):
        self.tag = tag

    def matches(self, node: Element):
        return isinstance(node, Element) and self.tag == node.name