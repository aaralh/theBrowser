from browser.elements.elements import DrawRect
from browser.globals import BrowserState
from browser.layouts.InlineLayout import InlineLayout
from typing import List
from browser.layouts.Layout import Layout
from browser.utils.logging import log
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
            # TODO: This is a hack to get around the fact that there is ghost elements in the DOM.
            if not child.name: continue
            if self.layout_mode(child) == "inline":
                next = InlineLayout(child, self, previous)
            else:
                next = BlockLayout(child, self, previous)
            self.children.append(next)
            previous = next

        self.width = self.parent.width

        self.x = self.parent.x
        if self.parent.border:
            self.x += self.parent.border.width

        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y
            if self.parent.border:
                self.y += self.parent.border.width

        for child in self.children:
            child.layout()

        self.calculate_size()

        if self.float == "right":
            self.x = self.parent.x + self.parent.width - self.width
            if self.previous and self.previous.float == "left":
                if self.previous.width + self.width <= self.parent.width:
                    self.y = self.previous.y
                else:
                    self.y = self.previous.y + self.previous.height
            for line in self.children:
                line.layout()
        elif self.float == "left":
            self.x = self.parent.x

        #self.height = sum([child.height for child in self.children])
