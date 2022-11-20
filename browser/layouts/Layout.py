from typing import List, Literal, Optional, Union
from browser.elements.elements import BorderProperties, DrawRect
from browser.globals import BrowserState
from browser.styling.color.utils import CSS_COLORS
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
        self.display_list = None
        self.dynamic_size = False

    def layout(self) -> None:
        raise NotImplementedError()

    def calculate_size(self) -> None:
        if not isinstance(self.node, Text):
            attr_height = self.node.style.get("height", "auto")

            if attr_height == "auto":
                self.height = sum([line.height for line in self.children])
            else:
                if attr_height.endswith("px"):
                    self.height = int(attr_height.replace("px", ""))
                elif attr_height.endswith("em"):
                    font_size = int(
                        self.node.style["font-size"].replace("px", ""))
                    self.height = float(
                        attr_height.replace("em", "")) * font_size

            attr_width = self.node.style.get("width", "auto")
            if "(" in attr_width:
                # TODO: Handle calc and other css functions.
                attr_width = "auto"
            if attr_width == "auto":
                self.width = self.parent.width
            else:
                if attr_width.endswith("px"):
                    self.width = int(attr_width.replace("px", ""))
                elif attr_width.endswith("em"):
                    font_size: str = self.node.style["font-size"]
                    if font_size.endswith("%"):
                        parent_font_size = int(self.parent.node.style["font-size"].replace("px", ""))
                        font_size = str((parent_font_size / 100) * int(font_size.replace("%", "")))
                    font_size = int(
                        round(float(font_size.replace("px", ""))))
                    self.width = int(attr_width.replace("em", "")) * font_size
                elif attr_width.endswith("%"):
                    self.dynamic_size = True
                    parent_width = self.parent.width
                    self.width = parent_width * \
                        (float(attr_width.replace("%", "")) / 100)
        else:
            self.height = sum([line.height for line in self.children])

    def recalculate_size(self) -> None:
        if self.dynamic_size:
            self.calculate_size()

        for child in self.children:
            child.recalculate_size()

    def layout_mode(self, node: Node) -> Literal["inline", "block"]:
        if isinstance(node, Text):
            return "inline"
        elif node.children:
            for child in node.children:
                if isinstance(child, Text): continue
                if child.name in BLOCK_ELEMENTS:
                    return "block"
            return "inline"
        else:
            return "block"
    
    def paint(self, display_list: list) -> None:
        if isinstance(self.node, Element):
                bgcolor = self.node.style.get("background-color",
                                        "transparent")
                border_style: Optional[str] = self.node.style.get("border", None)

                border = None

                if border_style:
                    styles = border_style.split(" ")
                    print("Styles", styles)
                    color = next(filter(lambda item: item.startswith("#") or item.startswith("rgb") or item in CSS_COLORS, styles), None)
                    width = next(filter(lambda item: item.endswith("%") or item.endswith("px") or item.endswith("em"), styles), "")
                    style = None
                    style_width = 0
                    if width.endswith("em"):
                        font_size = int(self.node.style["font-size"].replace("px", ""))
                        style_width = float(width.replace("em", "")) * font_size
                    elif width.endswith("%"):
                        style_width = self.parent.width * (int(width.replace("%", "")) / 100)
                    elif width.endswith("px"):
                        style_width = int(width[:-2])

                    print(width, style_width)

                    border = BorderProperties(width=style_width, color=color)


                if bgcolor == "unset":
                    try:
                        if isinstance(self.node.parentNode, Element):
                            bgcolor = self.node.parentNode.style.get("background-color",
                                        "transparent")
                    except:
                        bgcolor = "transparent"

                if bgcolor != "transparent":
                    x2, y2 = self.x + self.width, self.y + self.height
                    if str(self.node.id) in BrowserState.get_selected_elements():
                        rect = DrawRect(self.x, self.y, x2, y2, bgcolor, BorderProperties("red", 10))
                    elif border:
                        rect = DrawRect(self.x, self.y, x2, y2, bgcolor, border)
                    else:
                        rect = DrawRect(self.x, self.y, x2, y2, bgcolor)
                    display_list.append(rect)
                if str(self.node.id) in BrowserState.get_selected_elements():
                    x2, y2 = self.x + self.width, self.y + self.height
                    rect = DrawRect(self.x, self.y, x2, y2, "", BorderProperties("red", 10))
                elif border:
                    x2, y2 = self.x + self.width, self.y + self.height
                    print("Border color", border.color)
                    rect = DrawRect(self.x, self.y, x2, y2, "", border)

        for child in self.children:
            child.paint(display_list) 
