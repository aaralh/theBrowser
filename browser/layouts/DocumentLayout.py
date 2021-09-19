from web.dom.elements import HTMLBodyElement
from web.dom.DocumentType import DocumentType
from browser.layouts.Layout import Layout
from browser.layouts.BlockLayout import BlockLayout
import browser.globals as globals

class DocumentLayout(Layout):
    def __init__(self, node):
        self.node = node
        self.parent = None
        self.previous = None
        self.children = []

    def layout(self, screen_width):
        self.children = []
        body = self.__get_body(self.node)
        child = BlockLayout(body, self, None)
        self.children.append(child)
        self.width = screen_width - 2*globals.HSTEP
        self.x = globals.HSTEP
        self.y = globals.VSTEP
        child.layout()
        self.height = child.height + 2*globals.VSTEP

    def __get_body(self, dom: DocumentType) -> HTMLBodyElement:
        for child in dom.childNodes:
            for element in child.childNodes:
                if isinstance(element, HTMLBodyElement):
                    return element

    def paint(self, display_list: list):
        self.children[0].paint(display_list)