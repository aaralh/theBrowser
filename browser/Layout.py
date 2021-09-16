
from dataclasses import dataclass
from tkinter.font import Font
from typing import List
from web.dom.elements.Element import Element
from web.dom.elements import Text

@dataclass
class DOMElement():
    element: Element
    font: Font

class Layout:
    def __init__(self, elements: List[DOMElement], hstep, vstep, width):
        self.display_list = []
        self.hstep = hstep
        self.vstep = vstep
        self.width = width
        self.cursor_x = hstep
        self.cursor_y = vstep


        for element in elements:
            self.layout(element)

    def layout(self, element: DOMElement) -> None:
        if isinstance(element.element, Text):
            self.text(element.element, element.font)

    def text(self, element: Text, font: Font):
        for word in element.data.split():
            w = font.measure(word)
            if self.cursor_x + w >= self.width - self.hstep:
                self.cursor_y += font.metrics("linespace") * 1.2
                self.cursor_x = self.hstep
            self.display_list.append((self.cursor_x, self.cursor_y, word, font))
            self.cursor_x += w + font.measure(" ")