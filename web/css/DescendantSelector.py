from web.css.TagSelector import TagSelector
from web.dom.elements.Element import Element


class DescendantSelector:
    def __init__(self, ancestor: TagSelector, descendant: TagSelector):
        self.ancestor = ancestor
        self.descendant = descendant
        self.priority = ancestor.priority + descendant.priority

    def matches(self, node: Element):
        if not self.descendant.matches(node): return False
        while node.parentNode:
            if self.ancestor.matches(node.parentNode): return True
            node = node.parentNode
        return False
