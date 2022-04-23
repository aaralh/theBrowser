import os
from typing import List
from browser.elements.elements import DrawImage, DrawRect
from browser.layouts.Layout import Layout
from browser.layouts.LineLayout import LineLayout
from browser.layouts.TextLayout import TextLayout
from browser.layouts.table.TableDataInlineLayout import TableDataInlineLayout
from browser.utils.utils import resolve_url
from web.dom.Node import Node
from web.dom.elements.HTMLTdElement import HTMLTdElement
from io import BytesIO
from browser.utils.networking import request
from web.dom.elements import Text

class TableDataLayout(Layout):
    def __init__(self, node: Node, parent: Layout, previous: Layout):
        self.node = node
        self.children: List[TableDataInlineLayout] = []
        self.parent = parent
        self.previous = previous
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        self.font = None

    def previous_child(self) -> Layout:
        return self.children[-1] if len(self.children) > 0 else None

    def layout(self) -> None:
        self.width = self.parent.width / len(list(filter(lambda child: isinstance(child, HTMLTdElement), self.parent.node.children)))
        self.x = self.parent.x

        print("Data width:", self.width)
            
        if self.previous:
            space = 1
            self.x = self.previous.x + space + self.previous.width
        else:
            self.x = self.parent.x
            
        self.y = self.parent.y

        #for child in self.node.children:
        """ if isinstance(child, Text):
            if not line:
                line = LineLayout(self.node, self, None)
            print()
            print(child.data, self.previous_child(), self.x, self.y)
            print()
            text = TextLayout(child, child.data, self, self.previous_child())
            line.children.append(text) """
        inline_layout = TableDataInlineLayout(self.node, self, self.previous)
        inline_layout.layout()
        self.children.append(inline_layout)

        if not self.children:
            self.height = 0
            return

        self.height = sum([child.height for child in self.children]) 

    def paint(self, display_list: list) -> None:
        print("table data drawn")
        x2, y2 = self.x + self.width, self.y + self.height
        bgcolor = self.node.style.get("background-color",
                                      "transparent")
        if bgcolor != "transparent":
            display_list.append(DrawRect(self.x, self.y, x2, y2, bgcolor))

        for child in self.children:
            child.paint(display_list)
