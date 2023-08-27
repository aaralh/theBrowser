from typing import List
from browser.elements.elements import DrawRect, DrawText
from browser.layouts.Layout import Layout
from browser.layouts.utils import font_weight_to_string, get_font
from browser.styling.color.utils import transform_color
from web.dom.Node import Node
from web.dom.elements.Element import Element
from web.dom.elements.Text import Text

INPUT_WIDTH_PX = 200

class InputLayout(Layout):
    def __init__(self, node: Node, parent: Layout, previous: Layout):
        self.node = node
        self.parent = parent
        super().__init__()
        self.children = []
        self.previous = previous

    def layout(self):
        super().layout()
        weight = self.node.style["font-weight"]
        style = self.node.style["font-style"]
        if style == "normal": style = "roman"
        size = int(float(self.node.style["font-size"][:-2]) * .75)
        self.font = get_font(size, font_weight_to_string(weight), style)

        self.width = INPUT_WIDTH_PX

        if self.node.attributes.get("type", "") == "submit":
            text = self.node.attributes.get("value", None)
            if not text:
                text = self.node.attributes.get('alt', " ")
            self.width = self.font.measure(text)

        if self.previous:
            space = self.previous.font.measure(" ")
            self.x = self.previous.x + space + self.previous.width
        else:
            self.x = self.parent.x

        min_width = self.node.style.get("min-width", None)
        """if min_width:
            if min_width.endswith("px"):
                min_width = min_width.replace("px", "")
                if self.width < min_width:
                    self.width = min_width"""

        self.height = self.font.metrics("linespace")
       
    def paint(self, display_list: list):
        if self.node.attributes.get("type") == "hidden": return    
        
        bgcolor = self.node.style.get("background-color",
                                      "transparent")
        
        if bgcolor == "unset":
            try:
                if isinstance(self.node.parentNode, Element):
                    bgcolor = self.node.parentNode.style.get("background-color",
                                    "transparent")
            except:
                bgcolor = "transparent"

        if bgcolor != "transparent":
            x2, y2 = self.x + self.width, self.y + self.height
            if self.border:
                rect = DrawRect(self.x, self.y, x2, y2, transform_color(bgcolor), self.border)
            else:
                rect = DrawRect(self.x, self.y, x2, y2, transform_color(bgcolor))
            display_list.append(rect)

        if self.node.name == "input":
            text = self.node.attributes.get("value", None)
            if not text:
                text = self.node.attributes.get('alt', " ")
            if len(text) == 0:
                text = self.node.attributes.get("placeholder", "") 
        elif self.node.name == "button":
            visible_children: List[Node] = list(filter(lambda child: child.style.get("display") != "none", self.node.children))
            if len(visible_children) == 0: return
            child = visible_children[0]
            if isinstance(child, Text):
                text = child.data
            else:
                try:
                    text = child.children[0].data
                except:
                    text = ""
        
        color = self.node.style["color"]

        display_list.append(
            DrawText(self.x, self.y, text, self.font, color)
        )