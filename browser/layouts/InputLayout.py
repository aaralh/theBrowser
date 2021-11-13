from browser.elements.elements import DrawRect, DrawText
from browser.layouts.Layout import Layout
from browser.layouts.utils import get_font
from web.dom.Node import Node

INPUT_WIDTH_PX = 200

class InputLayout(Layout):
    def __init__(self, node: Node, parent: Layout, previous: Layout):
        self.node = node
        self.children = []
        self.parent = parent
        self.previous = previous

    def layout(self):
        weight = self.node.style["font-weight"]
        style = self.node.style["font-style"]
        if style == "normal": style = "roman"
        size = int(float(self.node.style["font-size"][:-2]) * .75)
        self.font = get_font(size, weight, style)

        self.width = INPUT_WIDTH_PX

        if self.node.attributes.get("type", "") == "submit":
            text = self.node.attributes.get("value", " ")
            self.width = self.font.measure(text)

        if self.previous:
            space = self.previous.font.measure(" ")
            self.x = self.previous.x + space + self.previous.width
        else:
            self.x = self.parent.x

        self.height = self.font.metrics("linespace")
       
    def paint(self, display_list: list):
        bgcolor = self.node.style.get("background-color",
                                      "transparent")
        if bgcolor != "transparent":
            x2, y2 = self.x + self.width, self.y + self.height
            rect = DrawRect(self.x, self.y, x2, y2, bgcolor)
            display_list.append(rect)

        if self.node.name == "input":
            print("INPUT")
            print(self.node.attributes)
            text = self.node.attributes.get("value", "")
            if len(text) == 0:
                text = self.node.attributes.get("placeholder", "") 
        elif self.node.name == "button":
            text = self.node.children[0].data

        print("Text:", text)
        
        color = self.node.style["color"]

        display_list.append(
            DrawText(self.x, self.y, text, self.font, color)
        )