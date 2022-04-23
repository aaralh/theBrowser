import os
from typing import List
from browser.elements.elements import DrawImage, DrawRect
from browser.layouts.Layout import Layout
from browser.layouts.table.TableRowLayout import TableRowLayout
from browser.utils.utils import resolve_url
from web.dom.Node import Node
from io import BytesIO
from browser.utils.networking import request

class TableBodyLayout(Layout):
    def __init__(self, node: Node, parent: Layout, previous: Layout):
        self.node = node
        self.children: List = []
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
        self.width = self.parent.width
        self.x = self.parent.x
            
        if self.previous:
            space = self.previous.font.measure(" ")
            self.x = self.previous.x + space + self.previous.width
        else:
            self.x = self.parent.x
            
        self.y = self.parent.y

        for child in self.node.children:
            if child.name == "tr":
                table_row = TableRowLayout(child, self, self.previous_child())
                table_row.layout()
                self.children.append(table_row)
        
        if not self.children:
            self.height = 0
            return
        
        self.height = sum([child.height for child in self.children]) 


    def paint(self, display_list: list) -> None:
        print("table drawn")
        x2, y2 = self.x + self.width, self.y + self.height
        bgcolor = self.node.style.get("background-color",
                                      "transparent")
        if bgcolor != "transparent":
            display_list.append(DrawRect(self.x, self.y, x2, y2, bgcolor))

        for child in self.children:
            child.paint(display_list)
