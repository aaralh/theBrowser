import os
from turtle import width
from typing import List
from browser.elements.elements import DrawImage
from browser.globals import BrowserState
from browser.layouts.Layout import Layout
from browser.utils.utils import resolve_url
from web.dom.Node import Node
from PIL import Image, ImageTk, UnidentifiedImageError
from io import BytesIO
from browser.utils.networking import request

class ImageLayout(Layout):
    def __init__(self, node: Node, parent: Layout, previous: Layout):
        self.node = node
        self.children: List = []
        self.parent = parent
        self.previous = previous
        self.image: ImageTk = None
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        self.font = None
        self.current_url = BrowserState.get_current_url()
        self.image_bytes = self.load_image()
    
    def load_image(self) -> bytes:
        image_src = self.node.attributes.get("src")
        src = resolve_url(image_src, self.current_url)
        response = request(src)
        return response.content

    def calculate_width(self) -> int:
        style_width = self.node.style.get("width", 100)
        attr_width = self.node.attributes.get("width")
        if attr_width:
            if attr_width.endswith("%"):
                attr_width = attr_width[:-1]
                return int(attr_width)
            return int(attr_width)

        return int(style_width)

    def calculate_height(self) -> int:
        style_height = self.node.style.get("height", 100)
        attr_height = self.node.attributes.get("height")
        if attr_height:
            if attr_height.endswith("%"):
                attr_height = attr_height[:-1]
                return int(attr_height)
            return int(attr_height)

        return int(style_height)

    def layout(self) -> None:
        try:
            image = Image.open(BytesIO(self.image_bytes))
        except UnidentifiedImageError:
            print(f"Image is not supported: Image path {self.node.attributes.get('src')}")
            image = Image.open('resources/images/not_allowed.jpg')
        
        height = self.calculate_height()
        width = self.calculate_width()

        image = image.resize((width, height))
        self.width = width if width else image.width
        self.height = height if height else image.height
        self.image = ImageTk.PhotoImage(image)
            
        if self.previous:
            space = 10
            self.x = self.previous.x + space + self.previous.width
        else:
            self.x = self.parent.x
            
        self.y = self.parent.y

    def paint(self, display_list: list) -> None:
        display_list.append(DrawImage(self.x, self.y, self.height, self.image))
