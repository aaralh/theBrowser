from typing import List, Literal, Optional, Union
from browser.elements.elements import BorderProperties, DrawRect
from browser.globals import BrowserState
from browser.styling.color.utils import CSS_COLORS, transform_color
from browser.styling.font.utils import CSS_FONTS_SIZE, convert_absolute_size_to_pixels
from web.dom.Node import Node
from web.dom.elements.Text import Text
from web.dom.elements.Element import Element

BLOCK_ELEMENTS = [
    "html", "body", "article", "section", "nav", "aside",
    "h1", "h2", "h3", "h4", "h5", "h6", "hgroup", "header",
    "footer", "address", "p", "hr", "pre", "blockquote",
    "ol", "ul", "menu", "li", "dl", "dt", "dd", "figure",
    "figcaption", "main", "div", "table", "form", "fieldset",
    "legend", "details", "summary"
]


class Layout:

    node: Element
    parent: 'Layout'
    children: List['Layout']

    x: int
    y: int
    width: int
    height: int

    def __init__(self):
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        # TODO: Rename this to something more sensible.
        self.internal_padding: int = 0
        self.display_list = None
        self.should_recalculate_size = False
        self.border = None
        self.font_size = self.calculate_font_size()
        self.float: Literal["none", "left", "right"] = self.node.style.get("float", "none")
        # Holds "real" height of the element. This is used  to calculate body height when elements children are floated.
        self.calculated_height: int = 0

    def calculate_font_size(self) -> int:
        font_size: str = self.node.style["font-size"]
        if font_size.endswith("%"):
            parent_font_size = self.parent.font_size
            font_size = str((parent_font_size / 100) * int(font_size.replace("%", "")))
        elif font_size.endswith("pt"):
            # TODO: Handle pt unit properly.
            font_size = str(int(font_size.replace("pt", "")) * 1.2)
        elif font_size in CSS_FONTS_SIZE:
            font_size = str(convert_absolute_size_to_pixels(font_size))
        elif font_size.endswith("em"):
            parent_font_size = self.parent.font_size
            font_size = str(parent_font_size * float(font_size.replace("em", "")))
        return int(round(float(font_size.replace("px", ""))))

    def layout(self) -> None:
        float_style = self.float
        if float_style in ["left", "right"]:
            #TODO: Add support for other float modes.
            self.float = float_style
        if isinstance(self.node, Element):
            self.create_border()

    def calculate_calculated_height(self) -> int:
        # Here child y and caculated_height might be None in initial layout cycle. With trycatch we can skip the first layout cycle and calculate the height in the second one.
        try:
            lowest_child_corner = max([child.y + child.calculated_height for child in self.children if child.y and child.calculated_height])
            return lowest_child_corner - self.y
        except:
            return 0


    def calculate_size(self) -> None:
        if not isinstance(self.node, Text):
            attr_height = self.node.style.get("height", "auto")
            if attr_height == "auto":
                self.calculated_height =  self.calculate_calculated_height()
                if self.float != "none":
                    self.height = sum([line.height for line in self.children])
                else:
                    self.height = sum([line.height for line in self.children if line.float == "none"])
            else:
                if attr_height.endswith("px"):
                    self.height = int(attr_height.replace("px", ""))
                elif attr_height.endswith("rem"):
                    #TODO: Fix rem and em calculations.
                    font_size = int(self.node.style["font-size"].replace("px", ""))
                    self.height = float(attr_height.replace("rem", "")) * font_size
                elif attr_height.endswith("em"):
                    font_size = int(self.node.style["font-size"].replace("px", ""))
                    self.height = float(attr_height.replace("em", "")) * font_size

                self.calculated_height = self.height

            attr_width = self.node.style.get("width", "auto")
            if "(" in attr_width:
                # TODO: Handle calc and other css functions.
                attr_width = "auto"
            if attr_width == "auto":
                if self.float != "none":
                    if len(self.children) > 0:
                        self.width = sum([child.width for child in self.children if child.width is not None])
                    else:
                        self.width = 0
                else:
                    self.width = self.parent.width
                    if self.parent.border:
                        self.width -= self.parent.border.width * 2
                """
                if self.float != "none":
                    if len(self.children) > 0:
                        self.width = sum([child.width for child in self.children])
                    else:
                        self.width = 0
                """
                if self.border:
                    self.width = self.width - self.border.width*2
            else:
                if attr_width.endswith("px"):
                    self.width = int(float(attr_width.replace("px", "")))
                elif attr_width.endswith("rem"):
                    font_size_str: str = self.node.style["font-size"]
                    if font_size_str.endswith("px"):
                        font_size = int(font_size_str.replace("px", ""))
                    elif font_size_str.endswith("%"):
                        parent_font_size = int(self.parent.node.style["font-size"].replace("px", ""))
                        font_size = ((parent_font_size / 100) * int(font_size_str.replace("%", "")))
                    elif font_size_str.endswith("rem"):
                        #TODO: Fix rem and em calculations.
                        parent_font_size = int(self.parent.node.style["font-size"].replace("px", ""))
                        font_size = str(parent_font_size * float(font_size_str.replace("rem", "")))
                    elif font_size_str.endswith("em"):
                        parent_font_size = int(self.parent.node.style["font-size"].replace("px", ""))
                        font_size = str(parent_font_size * float(font_size_str.replace("em", "")))
                    self.width = int(float(attr_width.replace("rem", ""))) * font_size
                elif attr_width.endswith("em"):
                    font_size_str: str = self.node.style["font-size"]
                    if font_size_str.endswith("px"):
                        font_size = int(font_size_str.replace("px", ""))
                    elif font_size_str.endswith("%"):
                        parent_font_size = int(self.parent.node.style["font-size"].replace("px", ""))
                        font_size = ((parent_font_size / 100) * int(font_size_str.replace("%", "")))
                    elif font_size_str.endswith("rem"):
                        #TODO: Fix rem and em calculations.
                        parent_font_size = int(self.parent.node.style["font-size"].replace("px", ""))
                        font_size = str(parent_font_size * float(font_size_str.replace("rem", "")))
                    elif font_size_str.endswith("em"):
                        parent_font_size = int(self.parent.node.style["font-size"].replace("px", ""))
                        font_size = str(parent_font_size * float(font_size_str.replace("em", "")))
                    self.width = int(float(attr_width.replace("em", ""))) * font_size
                elif attr_width.endswith("%"):
                    self.should_recalculate_size = True
                    parent_width = self.parent.width
                    self.width = int(parent_width * \
                        (float(attr_width.replace("%", "")) / 100))
                else:
                    self.width = int(attr_width)
        else:
            self.width = self.parent.width
            if self.parent.border:
                self.width -= self.parent.border.width * 2
            if self.float != "none":
                self.height = sum([line.height for line in self.children])
            else:
                self.height = sum([line.height for line in self.children if line.float == "none"])
            self.calculated_height = self.calculate_calculated_height()
        self.width = int(self.width + self.internal_padding*2)
        self.height = int(self.height + self.internal_padding*2)
        if self.calculated_height is not None:
            self.calculated_height = int(self.calculated_height + self.internal_padding*2)

    def recalculate_size(self) -> None:
        if self.should_recalculate_size:
            self.calculate_size()

        for child in self.children:
            child.recalculate_size()

    def update_layout(self, relayout_children: bool = False) -> None:
        #import pdb; pdb.set_trace()
        if self.relayout or relayout_children:
            print("Relayout", self)
            self.layout()
            for child in self.children:
                child.parent = self
                child.update_layout(True)
        else:
            print("not relayout", self)
            for child in self.children:
                child.update_layout()

    def layout_mode(self, node: Node) -> Literal["inline", "block"]:
        if isinstance(node, Text):
            return "inline"
        elif len(node.children) > 0:
            mode = "inline"
            for child in node.children:
                if isinstance(child, Text): continue
                if child.name in BLOCK_ELEMENTS:
                    mode =  "block"
            return mode
        else:
            return "block"

    def create_border(self) -> None:
        border_style: Optional[str] = self.node.style.get("border", None)

        if border_style:
            styles = border_style.split(" ")
            color = next(filter(lambda item: item.startswith("#") or item.startswith("rgb") or item in CSS_COLORS, styles), None)
            width = next(filter(lambda item: item.endswith("%") or item.endswith("px") or item.endswith("em"), styles), "")
            # TODO: Add support for border style.
            style = None
            border_width = 0
            if width.endswith("em"):
                font_size = int(self.node.style["font-size"].replace("px", ""))
                border_width = int(float(width.replace("em", "")) * font_size)
            elif width.endswith("%"):
                border_width = int(self.parent.width * (int(width.replace("%", "")) / 100))
            elif width.endswith("px"):
                border_width = int(width[:-2])

            if color:
                self.internal_padding = border_width
                self.border = BorderProperties(width=border_width, color=transform_color(color))

    def get_background_color(self):
        bgcolor = ""
        attr_color = self.node.attributes.get("bgcolor", None)
        if attr_color:
            return transform_color(attr_color).color
        background_style = self.node.style.get("background", None)
        if background_style:
            background_style = background_style.split(" ")
            color = next(filter(lambda item: item.startswith("#") or item.startswith("rgb") or item in CSS_COLORS, background_style), None)
            if color:
                return transform_color(color).color
        bgcolor = self.node.style.get("background-color", "transparent")
        return bgcolor

    def paint(self, display_list: list) -> None:
        if isinstance(self.node, Element):
            bgcolor = self.get_background_color()
            if bgcolor == "unset":
                try:
                    if isinstance(self.node.parentNode, Element):
                        bgcolor = self.node.parentNode.style.get("background-color",
                                    "transparent")
                except:
                    bgcolor = "transparent"

            if bgcolor != "transparent":
                bgcolor = transform_color(bgcolor)
                x2, y2 = self.x + self.width, self.y + self.height
                if str(self.node.id) in BrowserState.get_selected_elements():
                    rect = DrawRect(self.x, self.y, x2, y2, bgcolor, BorderProperties(transform_color("red"), 10))
                elif self.border:
                    rect = DrawRect(self.x, self.y, x2, y2, bgcolor, self.border)
                else:
                    rect = DrawRect(self.x, self.y, x2, y2, bgcolor)
                display_list.append(rect)
            if str(self.node.id) in BrowserState.get_selected_elements():
                x2, y2 = self.x + self.width, self.y + self.height
                rect = DrawRect(self.x, self.y, x2, y2, transform_color(""), BorderProperties(transform_color("red"), 10))
                display_list.append(rect)
            elif self.border:
                x2, y2 = self.x + self.width, self.y + self.height - self.border.width
                rect = DrawRect(self.x, self.y, x2, y2, transform_color(""), self.border)
                display_list.append(rect)

        for child in self.children:
            child.paint(display_list)
