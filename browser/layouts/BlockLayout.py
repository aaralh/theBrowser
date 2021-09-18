from web.dom.elements.Element import Element


class BlockLayout:
    def __init__(self, node: Element, parent: Element, previous: Element):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []

    def layout(self):
        previous = None
        for child in self.node.childNodes:
            next = BlockLayout(child, self, previous)
            self.children.append(next)
            previous = next