import os
from turtle import width
from typing import List
from browser.elements.elements import DrawImage
from browser.globals import BrowserState
from browser.layouts.Layout import Layout
from browser.styling.utils import style
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
        print("image:", src)
        return response.content

    def calculate_width(self) -> int:
        style_width = self.node.style.get("width", "auto")
        if (style_width.endswith("px")):
            style_width = style_width[:-2]
        elif (style_width.endswith("%")):
            style_width = self.parent.width * (int(style_width[:-1]) / 100)
        elif style_width == "auto":
            style_width = self.parent.width
        attr_width = self.node.attributes.get("width")
        if attr_width:
            if attr_width.endswith("%"):
                attr_width = attr_width[:-1]
                return int(attr_width)
            elif (attr_width.endswith("px")):
                attr_width = attr_width[:-2]
            return int(attr_width)

        return int(style_width)

    def calculate_height(self) -> int:
        style_height = self.node.style.get("height", "auto")
        attr_height = self.node.attributes.get("height")
        if attr_height:
            if attr_height.endswith("%"):
                attr_height = attr_height[:-1]
                return int(attr_height)
            elif (attr_height.endswith("px")):
                attr_height = attr_height[:-2]
            return int(attr_height)
        elif style_height == "auto":
            print("width", self.width)
            style_height = str(self.width)
        if style_height.endswith("px"):
            style_height = style_height[:-2]
        if style_height.endswith("%"):
            style_height = self.parent.height * (int(style_height[:-1]) / 100)
        return int(style_height)

    def layout(self) -> None:
        try:
            image = Image.open(BytesIO(self.image_bytes))
        except UnidentifiedImageError:
            print(f"Image is not supported: Image path {self.node.attributes.get('src')}")
            image = Image.open('resources/images/not_allowed.jpg')
        
        width = self.calculate_width()
        self.width = width
        height = self.calculate_height()
        self.height = height
        print("height/width", height, width)
        image = image.resize((width, height))
        self.image = ImageTk.PhotoImage(image)
            
        if self.previous:
            space = 10
            self.x = self.previous.x + space + self.previous.width
        else:
            self.x = self.parent.x
            
        self.y = self.parent.y

    def paint(self, display_list: list) -> None:
        display_list.append(DrawImage(self.x, self.y, self.height, self.image))
