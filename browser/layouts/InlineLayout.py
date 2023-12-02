from browser.layouts.ImageLayout import ImageLayout
from browser.layouts.InputLayout import INPUT_WIDTH_PX, InputLayout
from browser.layouts.dl.DescriptionListLayout import DescriptionListLayout
from web.dom.Node import Node
from browser.layouts.Layout import Layout
from dataclasses import dataclass
from tkinter.font import Font
from typing import List, Tuple, Union
from web.dom.elements.Element import Element
from web.dom.elements import Text
import browser.globals as globals
from browser.layouts.LineLayout import LineLayout
from browser.layouts.TextLayout import TextLayout
from browser.layouts.table.TableLayout import TableLayout
from browser.layouts.utils import font_weight_to_string, get_font
from web.dom.elements.HTMLDlElement import HTMLDlElement
from web.dom.elements.HTMLImgElement import HTMLImgElement
from web.dom.elements.HTMLInputElement import HTMLInputElement
from web.dom.elements.HTMLButtonElement import HTMLButtonElement
from web.dom.elements.HTMLTableElement import HTMLTableElement


@dataclass
class DOMElement():
    element: Element
    font: Font


class InlineLayout(Layout):
    def __init__(self, node: Node, parent: Layout, previous: Layout):
        self.node = node
        self.parent = parent
        super().__init__()
        self.previous = previous
        self.children = []
        self.height = 10

    def layout(self):
        super().layout()
        self.children = []
        self.width = self.parent.width
        self.x = self.parent.x + self.internal_padding

        if self.previous:
            self.y = self.previous.y + self.previous.calculated_height
        else:
            self.y = int(self.parent.y + self.internal_padding)

        if not self.previous and self.parent.border:
            self.y += self.parent.border.width

        self.new_line()
        self.recurse(self.node)

        for line in self.children:
            line.layout()


        self.calculate_size()

        if self.parent.border:
            self.width -= self.parent.border.width * 2

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


    def recurse(self, node: Node) -> None:
        display = node.style.get("display")
        if display == "none": return
        if isinstance(node, Text):
            self.text(node)
        elif isinstance(node, HTMLImgElement):
            print("image")
            if "src" in node.attributes:
                self.image(node)
                self.new_line()
        elif isinstance(node, HTMLTableElement):
            self.table(node)
            self.new_line()
        elif isinstance(node, HTMLDlElement):
            self.dl(node)
            self.new_line()
        else:
            if node.name == "br":
                self.new_line()
            elif node.name in ["input", "button"]:
                self.input(node)
            elif node.name in ["script", "style"]:
                pass
            else:
                for child in node.children:
                    self.recurse(child)

    def new_line(self):
        self.previous_word = None
        self.cursor_x = self.x
        last_line = self.children[-1] if self.children else None
        new_line = LineLayout(self.node, self, last_line)
        self.children.append(new_line)

    def image(self, element: HTMLImgElement):
        line = self.children[-1]
        image = ImageLayout(element, line, self.previous_word)
        self.children.append(image)

    def table(self, element: HTMLTableElement):
        line = self.children[-1]
        table = TableLayout(element, line, self.previous_word)
        self.children.append(table)

    def dl(self, element: HTMLTableElement):
        line = self.children[-1]
        table = DescriptionListLayout(element, line, self.previous_word)
        self.children.append(table)

    def input(self, element: Union[HTMLInputElement, HTMLButtonElement]):
        weight = element.style["font-weight"]
        style = element.style["font-style"]
        if style == "normal": style = "roman"
        size = int(float(element.style["font-size"][:-2]) * .75)
        font = get_font(size, font_weight_to_string(weight), style)
        w = INPUT_WIDTH_PX
        if self.cursor_x + w > self.x + self.width:
            self.new_line()
        line = self.children[-1]
        input = InputLayout(element, line, self.previous_word)
        line.children.append(input)
        self.previous_word = input
        self.cursor_x += w + font.measure(" ")

    def text(self, element: Text) -> None:
        weight = element.style["font-weight"]
        style = element.style["font-style"]
        if style == "normal": style = "roman"
        size = int(float(element.style["font-size"][:-2]) * .75)
        font = get_font(size, font_weight_to_string(weight), style)
        for word in element.data.split():
            w = font.measure(word)
            if self.parent.float == "none":
                if self.cursor_x + w > self.width - globals.HSTEP:
                    self.new_line()
            line = self.children[-1]
            text = TextLayout(element, word, line, self.previous_word)
            line.children.append(text)
            self.previous_word = text
            self.cursor_x += w + font.measure(" ")
