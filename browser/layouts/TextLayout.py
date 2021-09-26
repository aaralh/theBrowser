from web.dom.Node import Node
from browser.layouts.Layout import Layout
from tkinter.font import Font
from browser.layouts.utils import get_font
from browser.elements.elements import DrawText



class TextLayout(Layout):
    def __init__(self, node: Node, word: str, parent: Layout, previous: Layout):
        self.node = node
        self.word = word
        self.children = []
        self.parent = parent
        self.previous = previous

    def layout(self):
        weight = self.node.style["font-weight"]
        style = self.node.style["font-style"]
        if style == "normal": style = "roman"
        size = int(float(self.node.style["font-size"][:-2]) * .75)
        self.font = get_font(size, weight, style)

        self.width = self.font.measure(self.word)

        if self.previous:
            space = self.previous.font.measure(" ")
            self.x = self.previous.x + space + self.previous.width
        else:
            self.x = self.parent.x

        self.height = self.font.metrics("linespace")

    def paint(self, display_list: list):
        color = self.node.style["color"]
        display_list.append(DrawText(self.x, self.y, self.word, self.font, color))
