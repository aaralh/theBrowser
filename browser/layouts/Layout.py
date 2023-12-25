from typing import List, Literal, Optional, Union
from browser.elements.elements import Border, BorderProperties, DrawBorder, DrawRect
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

Side = Literal["top", "right", "bottom", "left"]

class Margin:

    def __init__(self):
        self.margins = {
            "top": 0,
            "right": 0,
            "bottom": 0,
            "left": 0
        }

    def set_margin(self, side: Side, value: int) -> None:
        self.margins[side] = value

    def get_margin(self, side: Side) -> int:
        return self.margins[side]

    def get_margins(self) -> dict:
        return self.margins

    @property
    def width(self) -> int:
        return self.margins["left"] + self.margins["right"]

    @property
    def height(self) -> int:
        return self.margins["top"] + self.margins["bottom"]

class Padding:

        def __init__(self):
            self.paddings = {
                "top": 0,
                "right": 0,
                "bottom": 0,
                "left": 0
            }

        def set_padding(self, side: Side, value: int) -> None:
            self.paddings[side] = value

        def get_padding(self, side: Side) -> int:
            return self.paddings[side]

        def get_paddings(self) -> dict:
            return self.paddings

        @property
        def width(self) -> int:
            return self.paddings["left"] + self.paddings["right"]

        @property
        def height(self) -> int:
            return self.paddings["top"] + self.paddings["bottom"]

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
        self.margin = Margin()
        self.border = Border()
        self.padding = Padding()
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
            self.create_margin()
            self.create_padding()

    def calculate_calculated_height(self) -> int:
        # Here child y and caculated_height might be None in initial layout cycle. With trycatch we can skip the first layout cycle and calculate the height in the second one.
        try:
            lowest_child_corner = max([child.y + child.calculated_height for child in self.children if child.y and child.calculated_height])
            return lowest_child_corner - (self.y + self.margin.get_margin("top") + self.padding.get_padding("top"))
        except:
            return 0


    def calculate_size(self) -> None:
        self.height = 0
        self.width = 0
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
                    self.width = self.parent.width - (self.parent.margin.width + self.parent.padding.width + self.parent.border.width) - (self.margin.width + self.padding.width + self.border.width)
                """
                if self.float != "none":
                    if len(self.children) > 0:
                        self.width = sum([child.width for child in self.children])
                    else:
                        self.width = 0
                """
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
            self.width = self.parent.width - (self.parent.margin.width + self.parent.padding.width + self.parent.border.width) - (self.margin.width + self.padding.width + self.border.width)
            if self.float != "none":
                self.height = sum([line.height for line in self.children])
            else:
                self.height = sum([line.height for line in self.children if line.float == "none"])
            self.calculated_height = self.calculate_calculated_height()
        self.width = int(int(self.width) + self.border.width + self.margin.width + self.padding.width)
        self.height = int(self.height + self.border.height + self.margin.height + self.padding.height)
        if self.calculated_height is not None:
            self.calculated_height = int(self.calculated_height + self.border.height + self.margin.height + self.padding.height)

    def recalculate_size(self) -> None:
        if self.should_recalculate_size:
            self.calculate_size()

        for child in self.children:
            child.recalculate_size()

    def update_layout(self, relayout_children: bool = False) -> None:
        #import pdb; pdb.set_trace()
        if self.relayout or relayout_children:
            self.layout()
            for child in self.children:
                child.parent = self
                child.update_layout(True)
        else:
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
        def calclulate_border_width(width: str) -> int:
            if width.endswith("em"):
                font_size = int(self.node.style["font-size"].replace("px", ""))
                return int(float(width.replace("em", "")) * font_size)
            elif width.endswith("%"):
                return int(self.parent.width * (int(width.replace("%", "")) / 100))
            elif width.endswith("px"):
                return int(width[:-2])
            else:
                return 0

        style = self.node.style

        if style.get("border", None):
            border_style = style.get("border", None)
            styles = border_style.split(" ")
            color = next(filter(lambda item: item.startswith("#") or item.startswith("rgb") or item in CSS_COLORS, styles), None)
            width = next(filter(lambda item: item.endswith("%") or item.endswith("px") or item.endswith("em"), styles), "")
            # TODO: Add support for border style.
            border_width = calclulate_border_width(width)

            if color:
                self.internal_padding = border_width
                for side in ["top", "right", "bottom", "left"]:
                    self.border.set_border(side, BorderProperties(width=border_width, color=transform_color(color)))
        elif style.get("border-width", None) and style.get("border-color", None):
            colors: Optional[str] = self.node.style.get("border-color", None)
            border_widths: Optional[str] = self.node.style.get("border-width", None)

            if colors and border_widths:
                widths: List[str] = list(filter(lambda item: item.endswith("%") or item.endswith("px") or item.endswith("em"), border_widths.split(" ")))
                #TODO: Handle multiple colors.
                color = colors.split(" ")[0]
                if len(widths) == 4:
                    for index, side in enumerate(["top", "right", "bottom", "left"]):
                        width = widths[index]
                        border_width = calclulate_border_width(width)
                        self.internal_padding = border_width
                        self.border.set_border(side, BorderProperties(width=border_width, color=transform_color(color)))
                elif len(widths) == 2:
                    for side in ["top", "bottom"]:
                        width = widths[0]
                        border_width = calclulate_border_width(width)
                        self.internal_padding = border_width
                        self.border.set_border(side, BorderProperties(width=border_width, color=transform_color(color)))
                    for side in ["right", "left"]:
                        width = widths[1]
                        border_width = calclulate_border_width(width)
                        self.internal_padding = border_width
                        self.border.set_border(side, BorderProperties(width=border_width, color=transform_color(color)))
                elif len(widths) == 1:
                    for side in ["top", "right", "bottom", "left"]:
                        width = widths[0]
                        border_width = calclulate_border_width(width)
                        self.internal_padding = border_width
                        self.border.set_border(side, BorderProperties(width=border_width, color=transform_color(color)))

        else:
            for side in ["top", "right", "bottom", "left"]:
                width = style.get(f"border-{side}-width", None)
                color = style.get(f"border-{side}-color", None)
                if width and color:
                    border_width = calclulate_border_width(width)
                    self.internal_padding = border_width
                    self.border.set_border(side, BorderProperties(width=border_width, color=transform_color(color)))

    def create_margin(self) -> None:
        def calculate_margin_width(width: str) -> int:
            if width.endswith("rem"):
                #TODO: Fix rem and em calculations.
                font_size = int(self.node.style["font-size"].replace("px", ""))
                return int(float(width.replace("rem", "")) * font_size)
            elif width.endswith("em"):
                font_size = int(self.node.style["font-size"].replace("px", ""))
                return int(float(width.replace("em", "")) * font_size)
            elif width.endswith("%"):
                return int(self.parent.width * (int(width.replace("%", "")) / 100))
            elif width.endswith("px"):
                return int(width[:-2])
            else:
                return 0

        style = self.node.style
        margin = style.get("margin", None)
        if margin:
            styles = margin.split(" ")
            widths = list(filter(lambda item: item.endswith("%") or item.endswith("px") or item.endswith("em") or item.isnumeric(), styles))
            if len(widths) == 4:
                for index, side in enumerate(["top", "right", "bottom", "left"]):
                    width = widths[index]
                    margin_width = calculate_margin_width(width)
                    self.margin.set_margin(side, margin_width)

            elif len(widths) == 2:
                for side in ["top", "bottom"]:
                    width = widths[0]
                    margin_width = calculate_margin_width(width)
                    self.margin.set_margin(side, margin_width)
                for side in ["right", "left"]:
                    width = widths[1]
                    margin_width = calculate_margin_width(width)
                    self.margin.set_margin(side, margin_width)
            elif len(widths) == 1:
                for side in ["top", "right", "bottom", "left"]:
                    width = widths[0]
                    margin_width = calculate_margin_width(width)
                    self.margin.set_margin(side, margin_width)
        else:
            for side in ["top", "right", "bottom", "left"]:
                width = style.get(f"margin-{side}", None)
                if width:
                    margin_width = calculate_margin_width(width)
                    self.margin.set_margin(side, margin_width)

    def create_padding(self) -> None:
        def calculate_padding_width(width: str) -> int:
            if width.endswith("rem"):
                #TODO: Fix rem and em calculations.
                font_size = int(self.node.style["font-size"].replace("px", ""))
                return int(float(width.replace("rem", "")) * font_size)
            elif width.endswith("em"):
                font_size = int(self.node.style["font-size"].replace("px", ""))
                return int(float(width.replace("em", "")) * font_size)
            elif width.endswith("%"):
                return int(self.parent.width * (int(float(width.replace("%", ""))) / 100))
            elif width.endswith("px"):
                return int(width[:-2])
            else:
                return 0

        style = self.node.style
        padding: Optional[str] = style.get("padding", None)
        if padding:
            styles = padding.split(" ")
            widths = list(filter(lambda item: item.endswith("%") or item.endswith("px") or item.endswith("em") or item.isnumeric(), styles))
            if len(widths) == 4:
                for index, side in enumerate(["top", "right", "bottom", "left"]):
                    #TODO: Handle individual margin widths
                    width = widths[index]
                    padding_width = calculate_padding_width(width)
                    self.padding.set_padding(side, padding_width)
            elif len(widths) == 2:
                for side in ["top", "bottom"]:
                    width = widths[0]
                    padding_width = calculate_padding_width(width)
                    self.padding.set_padding(side, padding_width)
                for side in ["right", "left"]:
                    width = widths[1]
                    padding_width = calculate_padding_width(width)
                    self.padding.set_padding(side, padding_width)
            elif len(widths) == 1:
                for side in ["top", "right", "bottom", "left"]:
                    width = widths[0]
                    padding_width = calculate_padding_width(width)
                    self.padding.set_padding(side, padding_width)
        else:
            for side in ["top", "right", "bottom", "left"]:
                width = style.get(f"padding-{side}", None)
                if width:
                    padding_width = calculate_padding_width(width)
                    self.padding.set_padding(side, padding_width)

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
            x = self.x + self.margin.get_margin("left")
            y = self.y + self.margin.get_margin("top")
            width = (self.width - self.margin.width)
            height = (self.height - self.margin.height)

            bgcolor = self.get_background_color()
            if bgcolor == "unset":
                try:
                    if isinstance(self.node.parentNode, Element):
                        bgcolor = self.node.parentNode.style.get("background-color",
                                    "transparent")
                except:
                    bgcolor = "transparent"

            x2, y2 = x + width, y + height
            if bgcolor != "transparent":
                bgcolor = transform_color(bgcolor)
                display_list.append(DrawRect(x, y, x2, y2, bgcolor))

            if str(self.node.id) in BrowserState.get_selected_elements():
                display_list.append(DrawRect(x, y, x2, y2, transform_color(""), ))
                border = Border()
                for side in ["top", "right", "bottom", "left"]:
                    border.set_border(side, BorderProperties(width=10, color=transform_color("red")))
                display_list.append(DrawBorder(x, y, x2, y2, border))
            else:
                display_list.append(DrawBorder(x, y, x2, y2, self.border))

        for child in self.children:
            child.paint(display_list)
