from browser.elements.elements import DrawRect
from browser.globals import BrowserState
from browser.layouts.InlineLayout import InlineLayout
from typing import List
from browser.layouts.Layout import Layout
from web.dom.elements.Element import Element
from browser.styling.utils import style

class BlockLayout(Layout):
    def __init__(self, node: Element, parent: Layout, previous: Layout):
        self.node = node
        self.parent = parent
        super().__init__()
        self.previous = previous
        self.children = []
        self.height = 10

    def layout(self):
        super().layout()
        self.children = []
        previous = None
        for child in self.node.children:
            display = child.style.get("display")
            if display == "none": continue            
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
        
        self.calculate_size()
        

        #self.height = sum([child.height for child in self.children])
