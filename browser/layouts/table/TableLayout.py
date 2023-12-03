from dataclasses import dataclass
import os
from tkinter.font import Font
from typing import List, Union, cast
from browser.elements.elements import DrawImage, DrawRect
from browser.layouts.ImageLayout import ImageLayout
from browser.layouts.InputLayout import INPUT_WIDTH_PX, InputLayout
from browser.layouts.Layout import Layout
from browser.layouts.LineLayout import LineLayout
from browser.layouts.TextLayout import TextLayout
from browser.layouts.utils import font_weight_to_string, get_font
from browser.utils.networking import resolve_url
from web.dom.Node import Node
from browser.utils.networking import request
from web.dom.elements import HTMLButtonElement, HTMLImgElement, HTMLInputElement
from web.dom.elements.Element import Element
from web.dom.elements.HTMLTableElement import HTMLTableElement
from web.dom.elements.HTMLTdElement import HTMLTdElement
from web.dom.elements.HTMLThElement import HTMLThElement
from web.dom.elements.Text import Text
import browser.globals as globals
from browser.utils.logging import log


class TableLayout(Layout):
    def __init__(self, node: Node, parent: Layout, previous: Layout):
        self.node = node
        self.parent = parent
        super().__init__()
        self.children: List = []
        self.previous = previous
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        self.font = None

    def previous_child(self) -> Layout:
        return self.children[-1] if len(self.children) > 0 else None

    def layout(self) -> None:
        super().layout()
        self.children = []
        width = self.node.style.get("width", self.node.attributes.get("width", str(self.parent.width)))
        if width.endswith("%"):
            width = self.parent.width * (int(width.replace("%", "")) / 100)
        elif width.endswith("em"):
            width = int(width.replace("em", "")) * self.font_size
        elif width.endswith("pt"):
            width = int(width.replace("pt", "")) * 1.33
        elif width == "auto":
            width = self.parent.width
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
        self.calculated_height = self.height

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


class TableBodyLayout(Layout):
    def __init__(self, node: Node, parent: Layout, previous: Layout):
        self.node = node
        self.parent = parent
        super().__init__()
        self.children: List = []
        self.previous = previous
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        self.font = None

    def previous_child(self) -> Layout:
        return self.children[-1] if len(self.children) > 0 else None

    def layout(self) -> None:
        super().layout()
        self.children = []
        self.width = self.parent.width
        self.x = self.parent.x

        if self.previous:
            """
            space = self.previous.font.measure(" ")
            """
            self.x = self.previous.x + self.previous.width
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
        self.node = node
        self.parent = parent
        super().__init__()
        self.children: List[TableDataLayout] = []
        self.previous = previous
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        self.font = None

    def previous_child(self) -> Layout:
        return self.children[-1] if len(self.children) > 0 else None

    def layout(self) -> None:
        super().layout()
        self.children = []
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

        contents_width = sum([child.width for child in self.children])
        if contents_width > self.width:
            dynamic_children = list(filter(lambda child: child.dynamic_width, self.children))
            non_dynamic_children = list(filter(lambda child: not child.dynamic_width, self.children))
            non_dynamic_width = sum([child.width for child in non_dynamic_children])
            available_width = self.width - non_dynamic_width
            for child in dynamic_children:
                child_width = (child.width/self.width) * available_width
                child.layout(child_width)

        elif contents_width < self.width:
            dynamic_children = list(filter(lambda child: child.dynamic_width, self.children))
            dynamic_children_width = sum([child.width for child in dynamic_children])
            available_width = self.width - dynamic_children_width
            non_dynamic_children = list(filter(lambda child: child.update_width, self.children))
            for child in self.children:
                if child.update_width:
                    child_width = available_width/len(non_dynamic_children)
                    child.layout(child_width)
                child.layout(child.width)


        if not self.children:
            self.height = 0
            return

        self.height = max([child.height for child in self.children])


class TableDataLayout(Layout):
    def __init__(self, node: Node, parent: Layout, previous: Layout):
        self.node = node
        self.parent = parent
        super().__init__()
        self.children: List[TableDataInlineLayout] = []
        self.previous = previous
        self.x = None
        self.y = None
        self.width = None
        self.orig_pixel_width = 0
        self.height = None
        self.font = None
        self.update_width = False
        self.dynamic_width = False

    def previous_child(self) -> Layout:
        return self.children[-1] if len(self.children) > 0 else None

    def calculate_width(self) -> int:
        attr_width = self.node.style.get("width", self.node.attributes.get("width"))
        log("Width", attr_width, len(self.node.children))
        if attr_width:
            if attr_width.endswith("%"):
                attr_width = int(attr_width.replace("%", ""))
                self.dynamic_width = True
                return self.parent.width * (attr_width/100)
            elif attr_width.endswith("px"):
                return int(attr_width.replace("px", ""))
            elif attr_width.endswith("em"):
                return int(attr_width.replace("em", "")) * self.font_size
            return int(attr_width)

        # TODO: Handle width of table data elements properly.
        # With this td elements with no contents are not taking unnecessary amount of horizontal space.
        if len(self.node.children) == 1 and isinstance(self.node.children[0], Text):
            if self.node.children[0].wholeText.isspace():
                return 0

        if len(self.node.children) > 0:
            # Calculate width of contents and reutrn min(content_widht, width below)
            self.update_width = True
            return self.parent.width / len(list(filter(lambda child: isinstance(child, HTMLTdElement) or isinstance(child, HTMLThElement), self.parent.node.children)))
        # TODO: Fix width calculations to take account margin, padding etc.
        return 0
        """
        child_count = len(list(filter(lambda child: isinstance(child, HTMLTdElement), self.parent.node.children)))
        return self.parent.width / child_count if child_count > 0 else 1
        """


    def calculate_size2(self) -> None:
        attr_height = self.node.style.get("height", "auto")

        if attr_height == "auto":
            self.height = sum([line.height for line in self.children])
        else:
            if attr_height.endswith("px"):
                self.height = int(attr_height.replace("px", ""))
            elif attr_height.endswith("em"):
                font_size = int(self.node.style["font-size"].replace("px", ""))
                self.height = float(attr_height.replace("em", "")) * font_size

        attr_width = self.node.style.get("width", "auto")
        if attr_width == "auto":
            self.width = self.parent.width
        else:
            if attr_width.endswith("px"):
                self.width = int(attr_width.replace("px", ""))
            elif attr_width.endswith("em"):
                font_size = int(self.node.style["font-size"].replace("px", ""))
                self.width = int(attr_width.replace("em", "")) * font_size
            elif attr_width.endswith("%"):
                parent_width = self.parent.width
                self.width = parent_width * (float(attr_width.replace("%", "")) / 100)

    def layout(self, width= None) -> None:
        super().layout()
        self.children = []
        if width:
            self.width = width
        else:
            self.width = self.calculate_width()
        self.orig_pixel_width = self.width
        log("Calculated width", self.width)
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
            log()
            log(child.data, self.previous_child(), self.x, self.y)
            log()
            text = TextLayout(child, child.data, self, self.previous_child())
            line.children.append(text) """
        inline_layout = TableDataInlineLayout(self.node, self, self.previous)
        inline_layout.layout()
        self.children.append(inline_layout)
        log("Table inline width", inline_layout.width)
        if not self.children:
            self.height = 0
            return

        if self.update_width:

            log("Udpated width", inline_layout.width)
            self.width = inline_layout.width

        self.height = sum([child.height for child in self.children])


@dataclass
class DOMElement():
    element: Element
    font: Font


class TableDataInlineLayout(Layout):
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

        self.height = sum([line.height for line in self.children])
        all_lines_empty = all([len(line.children) == 0 for line in filter(lambda child: isinstance(child, LineLayout), self.children)])
        other_content = list(filter(lambda child: not isinstance(child, LineLayout), self.children))
        log("Lines empty", all_lines_empty)

        if all_lines_empty and len(other_content) > 0:
            max_width = 0
            for item in other_content:
                if item.width > max_width:
                    max_width = item.width

            self.width = max_width

    def recurse(self, node: Node) -> None:
        if isinstance(node, Text):
            self.text(node)
        elif isinstance(node, HTMLImgElement):
            if "src" in node.attributes or "srcset" in node.attributes:
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
