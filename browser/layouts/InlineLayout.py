
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

@dataclass
class DOMElement():
    element: Element
    font: Font

FONTS = {}

def get_font(size, weight, slant) -> Font:
    key = (size, weight, slant)
    if key not in FONTS:
        font = Font(size=size, weight=weight, slant=slant)
        FONTS[key] = font
    return FONTS[key]

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

        self.display_list = []
        self.weight = "normal"
        self.style = "roman"
        self.size = 16

        self.cursor_x = self.x
        self.cursor_y = self.y
        self.line = []
        self.recurse(self.node)
        self.flush()

        self.height = self.cursor_y - self.y

    def recurse(self, node: Node) -> None:
        if isinstance(node, Text):
            self.text(node)
        elif node.name == "br":
            self.flush()
        else:
            self.open_tag(node.name)
            for child in node.childNodes:
                self.recurse(child)
            self.close_tag(node.name)

    def text(self, element: Text):
        font = get_font(self.size, self.weight, self.style)
        for word in element.data.split():
            w = font.measure(word)
            if self.cursor_x + w > self.width - globals.HSTEP:
                self.flush()
            self.line.append((self.cursor_x, word, font))
            self.cursor_x += w + font.measure(" ")

    def flush(self) -> None:
        if not self.line: return
        metrics = [font.metrics() for x, word, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent

        for x, word, font in self.line:
            y = baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font))

        self.cursor_x = self.x
        self.line = []
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent

    def open_tag(self, tag):
        if tag == "i":
            self.style = "italic"
        elif tag == "b" or tag == "strong":
            self.weight = "bold"
        elif tag == "small":
            self.size -= 2
        elif tag == "big":
            self.size += 4
        elif tag == "br":
            self.flush()

    def close_tag(self, tag):
        if tag == "i":
            self.style = "roman"
        elif tag == "b" or tag == "strong":
            self.weight = "normal"
        elif tag == "small":
            self.size += 2
        elif tag == "big":
            self.size -= 4
        elif tag == "p":
            self.flush()
            self.cursor_y += globals.VSTEP

    def paint(self, display_list: list):
        
        if isinstance(self.node, Element):
            bgcolor = self.node.style.get("background-color",
                                      "transparent")
            if bgcolor != "transparent":
                x2, y2 = self.x + self.width, self.y + self.height
                rect = DrawRect(self.x, self.y, x2, y2, bgcolor)
                display_list.append(rect)

        for x, y, word, font in self.display_list:
            display_list.append(DrawText(x, y, word, font))
