from web.dom.Node import Node
from browser.layouts.Layout import Layout


class LineLayout(Layout):
    def __init__(self, node: Node, parent: Layout, previous: Layout):
        self.node = node
        self.parent = parent
        super().__init__()
        self.previous = previous
        self.children = []
        self.x = None
        self.y = None
        self.width = None
        self.height = None

    def layout(self):
        super().layout()
        self.width = self.parent.width
        self.x = self.parent.x

        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y
            self.x = self.x + self.parent.internal_padding

        for word in self.children:
            word.layout()

        if self.width == 0:
            self.width = sum([word.width for word in self.children])

        if len(self.children) == 0:
            self.height = 0
            return

        max_ascent = max([word.font.metrics("ascent") for word in self.children])
        baseline = self.y + 1.25 * max_ascent

        for word in self.children:
            word.y = baseline - word.font.metrics("ascent")

        max_descent = max([word.font.metrics("descent") for word in self.children])
        self.height = 1.25 * (max_ascent + max_descent)
        self.calculated_height = self.height

    def paint(self, display_list: list):
        for child in self.children:
            child.paint(display_list)
