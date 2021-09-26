
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
        else:
            if node.name == "br":
                self.flush()
            for child in node.childNodes:
                self.recurse(child)

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
                self.flush()
            self.line.append((self.cursor_x, word, font, color))
            self.cursor_x += w + font.measure(" ")

    def flush(self) -> None:
        if not self.line: return
        metrics = [font.metrics() for x, word, font, color in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent

        for x, word, font, color in self.line:
            y = baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font, color))

        self.cursor_x = self.x
        self.line = []
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent

    def paint(self, display_list: list):
        if isinstance(self.node, Element):
            bgcolor = self.node.style.get("background-color",
                                      "transparent")
            if bgcolor != "transparent":
                x2, y2 = self.x + self.width, self.y + self.height
                rect = DrawRect(self.x, self.y, x2, y2, bgcolor)
                display_list.append(rect)

        for x, y, word, font, color in self.display_list:
            display_list.append(DrawText(x, y, word, font, color))

