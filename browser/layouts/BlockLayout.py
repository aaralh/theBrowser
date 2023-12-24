from tkinter import W
from browser.elements.elements import DrawRect
from browser.globals import BrowserState
from browser.layouts.InlineLayout import InlineLayout
from typing import List
from browser.layouts.Layout import Layout
from browser.utils.logging import log
from web.dom.elements.Element import Element
from browser.styling.utils import style
from web.dom.elements.Text import Text

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

        self.calculate_size()

        self.x = self.parent.x + self.parent.margin.get_margin("left") + self.parent.border.get_border("left").width + self.parent.padding.get_padding("left")

        if self.previous:
            self.y = self.previous.y + self.previous.calculated_height
        else:
            self.y = self.parent.y + self.parent.margin.get_margin("top") + self.parent.border.get_border("top").width + self.parent.padding.get_padding("top")

        for child in self.children:
            child.layout()

        self.calculate_size()

        if self.node.name == "body":
            self.height = self.calculated_height
            for child in self.children:
                child.layout()

        if self.float == "right":
            self.x = self.parent.x + self.parent.width - self.width
            if self.previous and self.previous.float == "left":
                if self.width < (self.parent.x + self.parent.width) - (self.previous.x + self.previous.width):
                    self.y = self.previous.y
                else:
                    self.y = self.previous.y + self.previous.height
            for line in self.children:
                line.layout()
        elif self.float == "left":
            if self.previous and self.previous.float == "left":
                if self.width < (self.parent.x + self.parent.width) - (self.previous.x + self.previous.width):
                    self.y = self.previous.y
                    self.x = self.previous.x + self.previous.width
                else:
                    self.y = self.previous.y + self.previous.height
            elif self.parent and self.previous and self.parent.float != "none" and self.previous.float == "none":
                self.x = self.previous.children[-1].x + self.previous.children[-1].width

                if self.width < (self.parent.x + self.parent.width) - (self.previous.children[-1].x + self.previous.children[-1].width):
                    self.y = self.previous.children[-1].y
                else:
                    self.y = self.previous.children[-1].y + self.previous.children[-1].height
            else:
                self.x = self.parent.x + self.parent.margin.get_margin("left") + self.parent.padding.get_padding("left")
            for line in self.children:
                line.layout()

        #self.height = sum([child.height for child in self.children])
