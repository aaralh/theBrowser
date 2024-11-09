from browser.globals import BrowserState
from browser.styling.color import transform_color
from web.dom.Node import Node
from browser.layouts.Layout import Layout
from browser.layouts.utils import font_weight_to_string, get_font
from browser.elements.elements import BorderProperties, DrawRect, DrawText



class TextLayout(Layout):
    def __init__(self, node: Node, word: str, parent: Layout, previous: Layout):
        self.node = node
        self.parent = parent
        super().__init__()
        self.word = word
        self.children = []
        self.previous = previous
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        self.font = None

    def layout(self) -> None:
        super().layout()
        weight = self.node.style["font-weight"]
        style = self.node.style["font-style"]
        if style == "normal": style = "roman"
        if str(self.node.style["font-size"]).endswith("px"):
            size = int(float(self.node.style["font-size"][:-2]) * .75)
        elif str(self.node.style["font-size"]).endswith("%"):
            multiplier = int(self.node.style["font-size"][:-1]) / 100
            size = int(self.parent.font_size * multiplier)
        else:
            # This is just a temporary default value.
            size = int(float(16) * .75)
        self.font = get_font(size, font_weight_to_string(weight), style)

        self.width = self.font.measure(self.word)

        if self.previous:
            space = self.previous.font.measure(" ")
            self.x = self.previous.x + space + self.previous.width
        else:
            self.x = self.parent.x + self.internal_padding

        self.height = self.font.metrics("linespace")

    def paint(self, display_list: list) -> None:
        color = self.node.style["color"]
        display_list.append(DrawText(self.x, self.y, self.word, self.font, color))

        if str(self.node.id) in BrowserState.get_selected_elements():
            x2, y2 = self.x + self.width, self.y + self.height
            rect = DrawRect(self.x, self.y, x2, y2, "", BorderProperties(transform_color("red"), 10))
            display_list.append(rect)
