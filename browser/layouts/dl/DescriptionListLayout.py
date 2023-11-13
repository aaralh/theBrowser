from typing import List
from browser.elements.elements import DrawRect
from browser.layouts.Layout import Layout
from browser.layouts.dl.DescriptionListItemLayout import DescriptionListItemLayout
from web.dom.Node import Node
from web.dom.elements import Text


class DescriptionListLayout(Layout):
    def __init__(self, node: Node, parent: Layout, previous: Layout):
        self.node = node
        self.parent = parent
        super().__init__()
        self.children: List = []
        self.previous = previous
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        self.font = None

    def previous_child(self) -> Layout:
        return self.children[-1] if len(self.children) > 0 else None

    def layout(self) -> None:
        super().layout()
        width = self.node.attributes.get("width", str(self.parent.width))
        if width.endswith("%"):
            width = self.parent.width * (int(width[:-1]) / 100)
        self.width = int(float(width))
        self.x = self.parent.x

        if self.previous:
            space = self.previous.font.measure(" ")
            self.x = self.previous.x + space + self.previous.width
        else:
            self.x = self.parent.x

        self.y = self.parent.y

        for child in self.node.children:
            display = child.style.get("display")
            if display == "none": continue
            table_row = DescriptionListItemLayout(child, self, self.previous_child())
            table_row.layout()
            self.children.append(table_row)

        if not self.children:
            self.height = 0
            return

        self.height = sum([child.height for child in self.children])
        if self.float == "right":
            self.x = self.parent.x + self.parent.width - self.width
            if self.previous and self.previous.float == "left":
                if self.width < (self.parent.width - (self.previous.x + self.previous.width)):
                    self.y = self.previous.y
                else:
                    self.y = self.previous.y + self.previous.height
            for line in self.children:
                line.layout()
        elif self.float == "left":
            if self.previous and self.previous.float == "left":
                if self.width < (self.parent.width - ((self.previous.x + self.previous.width) - self.parent.x)):
                    self.y = self.previous.y
                    self.x = self.previous.x + self.previous.width
                else:
                    self.y = self.previous.y + self.previous.height
            else:
                self.x = self.parent.x
            for line in self.children:
                line.layout()
