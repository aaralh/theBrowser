from dataclasses import dataclass
import os
from tkinter.font import Font
from typing import List, Union
from browser.elements.elements import DrawImage, DrawRect
from browser.layouts.ImageLayout import ImageLayout
from browser.layouts.InputLayout import INPUT_WIDTH_PX, InputLayout
from browser.layouts.Layout import Layout
from browser.layouts.LineLayout import LineLayout
from browser.layouts.TextLayout import TextLayout
from browser.layouts.utils import font_weight_to_string, get_font
from browser.utils.utils import resolve_url
from web.dom.Node import Node
from browser.utils.networking import request
from web.dom.elements import HTMLButtonElement, HTMLImgElement, HTMLInputElement
from web.dom.elements.Element import Element
from web.dom.elements.HTMLTableElement import HTMLTableElement
from web.dom.elements.HTMLTdElement import HTMLTdElement
from web.dom.elements.HTMLThElement import HTMLThElement
from web.dom.elements.Text import Text
import browser.globals as globals


class TableLayout(Layout):
    def __init__(self, node: Node, parent: Layout, previous: Layout):
        super().__init__()

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
        width = self.node.attributes.get("width", str(self.parent.width))
        if width.endswith("%"):
            width = self.parent.width * (int(width[:-1]) / 100)
        self.width = int(float(width))
        self.x = self.parent.x
            
        if self.previous:
            space = self.previous.font.measure(" ")
            self.x = self.previous.x + space + self.previous.width
        else:
            self.x = self.parent.x
            
        self.y = self.parent.y

        for child in self.node.children:
            display = child.style.get("display")
            if display == "none": continue
            if child.name == "tr":
                table_row = TableRowLayout(child, self, self.previous_child())
                table_row.layout()
                self.children.append(table_row)
            elif child.name == "tbody":
                table_row = TableBodyLayout(child, self, self.previous_child())
                table_row.layout()
                self.children.append(table_row)

        if not self.children:
            self.height = 0
            return
        
        self.height = sum([child.height for child in self.children]) 
        


class TableBodyLayout(Layout):
    def __init__(self, node: Node, parent: Layout, previous: Layout):
        super().__init__()

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
            display = child.style.get("display")
            if display == "none": continue
            if child.name == "tr":
                table_row = TableRowLayout(child, self, self.previous_child())
                table_row.layout()
                self.children.append(table_row)
        
        if not self.children:
            self.height = 0
            return
        
        self.height = sum([child.height for child in self.children]) 


class TableRowLayout(Layout):
    def __init__(self, node: Node, parent: Layout, previous: Layout):
        super().__init__()

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
            space = 1
            self.y = self.previous.y + space + self.previous.height
        else:
            self.y = self.parent.y

        for child in self.node.children:
            display = child.style.get("display")
            if display == "none": continue

            if child.name == "td":
                table_row = TableDataLayout(child, self, self.previous_child())
                self.children.append(table_row)
            elif child.name == "th":
                table_row = TableDataLayout(child, self, self.previous_child())
                self.children.append(table_row)

        for child in self.children:
            child.layout()

        if not self.children:
            self.height = 0
            return
        
        self.height = max([child.height for child in self.children]) 


class TableDataLayout(Layout):
    def __init__(self, node: Node, parent: Layout, previous: Layout):
        super().__init__()

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

    def calculate_width(self) -> int:
        attr_width = self.node.attributes.get("width")
        if attr_width:
            if attr_width.endswith("%"):
                attr_width = int(attr_width[:-1])
                return self.parent.width * (attr_width/100)
            return int(attr_width)
        return self.parent.width / len(list(filter(lambda child: isinstance(child, HTMLTdElement) or isinstance(child, HTMLThElement), self.parent.node.children)))

        """
        child_count = len(list(filter(lambda child: isinstance(child, HTMLTdElement), self.parent.node.children)))
        return self.parent.width / child_count if child_count > 0 else 1
        """

    def layout(self) -> None:
       
        self.width = self.calculate_width()
        self.x = self.parent.x
            
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
        x2, y2 = self.x + self.width, self.y + self.height
        bgcolor = self.node.style.get("background-color",
                                      "transparent")
        if bgcolor != "transparent":
            display_list.append(DrawRect(self.x, self.y, x2, y2, bgcolor))

        for child in self.children:
            child.paint(display_list)

@dataclass
class DOMElement():
    element: Element
    font: Font


class TableDataInlineLayout(Layout):
    def __init__(self, node: Node, parent: Layout, previous: Layout):
        super().__init__()

        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []

    def layout(self):
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

        self.height = sum([line.height for line in self.children]) 

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
