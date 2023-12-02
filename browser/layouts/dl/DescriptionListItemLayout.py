from typing import Union
from browser.elements.elements import DrawRect
from browser.layouts.ImageLayout import ImageLayout
from browser.layouts.InputLayout import INPUT_WIDTH_PX, InputLayout
from browser.layouts.Layout import Layout
from browser.layouts.LineLayout import LineLayout
from browser.layouts.TextLayout import TextLayout
from browser.layouts.utils import font_weight_to_string, get_font
from web.dom.Node import Node
from web.dom.elements import HTMLButtonElement, HTMLImgElement, HTMLInputElement
from web.dom.elements.Element import Element
from web.dom.elements.HTMLTableElement import HTMLTableElement
from web.dom.elements.Text import Text
import browser.globals as globals

class DescriptionListItemLayout(Layout):
    def __init__(self, node: Node, parent: Layout, previous: Layout):
        self.node = node
        self.parent = parent
        super().__init__()
        self.previous = previous
        self.children = []

    def layout(self):
        super().layout()
        self.children = []
        self.width = self.parent.width
        self.x = self.parent.x

        if self.previous:
            self.y = self.previous.y
        else:
            self.y = self.parent.y

        self.new_line()
        self.recurse(self.node)
        for line in self.children:
            line.layout()

        attr_height = self.node.style.get("height", "auto")

        if attr_height == "auto":
            self.height = sum([line.height for line in self.children])
        else:
            if attr_height.endswith("px"):
                self.height = int(attr_height.replace("px", ""))
            elif attr_height.endswith("em"):
                font_size = self.node.style["font-size"]
                self.height = int(attr_height.replace("em", "")) * font_size

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
        self.calculated_height = self.height

    def recurse(self, node: Node) -> None:
        if isinstance(node, Text):
            self.text(node)
        elif isinstance(node, HTMLImgElement):
            if "src" in node.attributes:
                self.image(node)
                self.new_line()
        elif isinstance(node, HTMLTableElement):
            self.table(node)
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
        last_line = self.children[-1] if len(self.children) > 0 else None
        new_line = LineLayout(self.node, self, last_line)
        self.children.append(new_line)

    def image(self, element: HTMLImgElement):
        line = self.children[-1]
        image = ImageLayout(element, line, self.previous_word)
        self.previous_word = image
        self.children.append(image)

    def table(self, element: HTMLTableElement):
        line = self.children[-1]
        table = TableLayout(element, line, self.previous_word)
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
        if element.data.isspace(): return
        weight = element.style["font-weight"]
        style = element.style["font-style"]
        if style == "normal": style = "roman"
        if not str(element.style["font-size"]).endswith("px"):
            # This is just a temporary default value.
            size = int(float(16) * .75)
        else:
            size = int(float(element.style["font-size"][:-2]) * .75)
        font = get_font(size, font_weight_to_string(weight), style)
        for word in element.data.split():
            w = font.measure(word)
            if self.cursor_x + w > (self.width + self.x) - globals.HSTEP:
                self.new_line()
            line = self.children[-1]
            text = TextLayout(element, word, line, self.previous_word)
            line.children.append(text)
            self.previous_word = text
            self.cursor_x += w + font.measure(" ")
