
from dataclasses import dataclass
from tkinter.font import Font
from typing import List
from web.dom.elements.Element import Element
from web.dom.elements import Text

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

class Layout:
    def __init__(self, elements: List[DOMElement], hstep, vstep, width):
        self.display_list = []
        self.hstep = hstep
        self.vstep = vstep
        self.width = width
        self.cursor_x = hstep
        self.cursor_y = vstep
        self.line = []

        for element in elements:
            if element.element.name == "script":
                continue

            self.layout(element)

        self.flush()

    def layout(self, element: DOMElement) -> None:
        if isinstance(element.element, Text):
            self.text(element.element, element.font)
        elif element.element.name == "br":
            self.flush()

    def text(self, element: Text, font: Font):
        #font = get_font(self.size, self.weight, self.style)
        for word in element.data.split():
            w = font.measure(word)
            if self.cursor_x + w >= self.width - self.hstep:
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

        self.cursor_x = self.hstep
        self.line = []
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent
