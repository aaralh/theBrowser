
from browser.styling.CSSParser import CSSParser
from browser.elements.elements import DrawRect, DrawText
from web.dom.Node import Node
from browser.layouts.Layout import Layout
from dataclasses import dataclass
from tkinter.font import Font
from typing import List, Tuple
from web.dom.elements.Element import Element
from web.dom.elements import Text
import browser.globals as globals
from browser.layouts.LineLayout import LineLayout
from browser.layouts.TextLayout import TextLayout
from browser.layouts.utils import get_font

@dataclass
class DOMElement():
    element: Element
    font: Font


class InlineLayout(Layout):
    def __init__(self, node: Node, parent: Layout, previous: Layout):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []

    def layout(self):
        self.children = []
        self.width = self.parent.width
        self.x = self.parent.x

        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y

        self.new_line()
        self.recurse(self.node)
        
        for line in self.children:
            line.layout()

        self.height = sum([line.height for line in self.children]) 

    def recurse(self, node: Node) -> None:
        if isinstance(node, Text):
            self.text(node)
        else:
            if node.name == "br":
                self.new_line()
            for child in node.children:
                self.recurse(child)

    def new_line(self):
        self.previous_word = None
        self.cursor_x = self.x
        last_line = self.children[-1] if self.children else None
        new_line = LineLayout(self.node, self, last_line)
        self.children.append(new_line)

    def text(self, element: Text):
        weight = element.style["font-weight"]
        style = element.style["font-style"]
        if style == "normal": style = "roman"
        size = int(float(element.style["font-size"][:-2]) * .75)
        color = element.style["color"]
        font = get_font(size, weight, style)
        for word in element.data.split():
            w = font.measure(word)
            if self.cursor_x + w > self.width - globals.HSTEP:
                self.new_line()
            line = self.children[-1]
            text = TextLayout(element, word, line, self.previous_word)
            line.children.append(text)
            self.previous_word = text
            self.cursor_x += w + font.measure(" ")


    def paint(self, display_list: list):
        if isinstance(self.node, Element):
            bgcolor = self.node.style.get("background-color",
                                      "transparent")
            if bgcolor != "transparent":
                x2, y2 = self.x + self.width, self.y + self.height
                rect = DrawRect(self.x, self.y, x2, y2, bgcolor)
                display_list.append(rect)

        for child in self.children:
            child.paint(display_list)
