from browser.layouts.InlineLayout import InlineLayout
from typing import List
from browser.layouts.Layout import Layout
from web.dom.elements.Element import Element
from browser.styling.utils import style

class BlockLayout(Layout):
    def __init__(self, node: Element, parent: Layout, previous: Layout):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []

    def layout(self):
        self.children = []
        previous = None
        for child in self.node.children:
            if self.layout_mode(child) == "inline":
                next = InlineLayout(child, self, previous)
            else:
                next = BlockLayout(child, self, previous)
            self.children.append(next)
            previous = next

        self.width = self.parent.width
        self.x = self.parent.x

        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y

        for child in self.children:
            child.layout()
        
        self.height = sum([child.height for child in self.children])

    def paint(self, display_list):
        for child in self.children:
            child.paint(display_list)
