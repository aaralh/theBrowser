from typing import TypeVar, cast
from browser.elements.elements import DrawRect
from browser.styling.color.utils import transform_color
from web.dom.elements import HTMLBodyElement
from web.dom.DocumentType import DocumentType
from browser.layouts.Layout import Layout
from browser.layouts.BlockLayout import BlockLayout
import browser.globals as globals
from web.dom.elements.Element import Element
from web.dom.elements.HTMLElement import HTMLElement
from browser.utils.logging import log

T = TypeVar('T')

class DocumentLayout(Layout):
    def __init__(self, node):
        self.node = node
        self.parent = None
        self.previous = None
        self.children = []
        self.body = self.__get_element(node, HTMLBodyElement)
        self.html = self.__get_element(node, HTMLElement)
        self.content_height = 0

    def layout(self, screen_width):
        super().layout()
        self.children = []
        self.html.__children = [self.body]
        log("Node:", self.body.name)
        child = BlockLayout(self.body, self, None)
        self.children.append(child)
        self.width = int(float(screen_width - 2*globals.HSTEP))
        self.x = globals.HSTEP
        self.y = globals.VSTEP
        child.layout()
        child.recalculate_size()
        self.content_height = child.height + 2*globals.VSTEP

    def __get_element(self, dom: DocumentType, type: T) -> T:
        for child in dom.children:
            if isinstance(child, cast(Element, type)):
                    return child
            for element in child.children:
                if isinstance(element, cast(Element, type)):
                    return element

    def paint(self, display_list: list):
        bgcolor = self.html.style.get("background-color",
                                    None)
        if not bgcolor:
            bgcolor = self.html.style.get("background",
                                    "transparent")


        log("HTML", bgcolor)
        if bgcolor != "transparent":
            x2, y2 = self.x + self.width, self.y + self.height
            rect = DrawRect(self.x, self.y, x2, y2, transform_color(bgcolor))
            display_list.append(rect)
        self.children[0].paint(display_list)
