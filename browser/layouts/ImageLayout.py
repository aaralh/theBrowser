import os
from turtle import width
from typing import List
from browser.elements.elements import DrawImage
from browser.globals import BrowserState
from browser.layouts.Layout import Layout
from browser.styling.utils import style
from browser.utils.networking import resolve_url
from web.dom.Node import Node
from PIL import Image, ImageTk, UnidentifiedImageError
from io import BytesIO
from browser.utils.networking import request
from browser.utils.logging import log

# Workaround for apple m chip macs to be able to laod cairosvg.
from ctypes.macholib import dyld
dyld.DEFAULT_LIBRARY_FALLBACK.append("/opt/homebrew/lib")
from cairosvg import svg2png

class ImageLayout(Layout):
    def __init__(self, node: Node, parent: Layout, previous: Layout):
        self.node = node
        self.parent = parent
        super().__init__()
        self.children: List = []
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
        if not image_src:
            srcset = self.node.attributes.get("srcset")
            if srcset:
                try:
                    src = srcset.split(",")[0].split(" ")[0]
                    image_src = src
                except:
                    log("srcset is faulty!")

        log("image:", image_src, self.current_url)
        try:
            src = resolve_url(image_src, self.current_url)
            log("image:", src, image_src, self.current_url)
            if src.endswith(".svg"):
                return svg2png(url=src)
            else:
                try:
                    response = request(src)
                    return response.content
                except:
                    log("Image not found!")
        except:
            log("Could not resolve url!")

    def calculate_width(self) -> int:
        style_width = self.node.style.get("width", None)
        attr_width = self.node.attributes.get("width", None)

        if not style_width and not attr_width:
            return self.height
        if style_width:
            style_width = str(style_width)
            if (style_width.endswith("px")):
                style_width = style_width[:-2]
            elif (style_width.endswith("%")):
                style_width = self.parent.width * (int(style_width[:-1]) / 100)
            elif style_width == "auto":
                style_width = self.parent.width
            elif style_width.endswith("rem"):
                #TODO: Fix rem and em calculation.
                font_size = self.font_size
                style_width = int(float(style_width.replace("rem", "")) * font_size)
            elif style_width.endswith("em"):
                font_size = self.font_size
                style_width = int(float(style_width.replace("em", "")) * font_size)
        if attr_width:
            if attr_width.endswith("%"):
                self.should_recalculate_size = True
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
            if self.width == None:
                return 100
            style_height = str(self.width)
        if style_height.endswith("px"):
            style_height = style_height[:-2]
        elif style_height.endswith("%"):
            self.should_recalculate_size = True
            style_height = self.parent.height * (int(style_height[:-1]) / 100)
        elif style_height.endswith("rem"):
            #TODO: Fix rem and em calculation.
            font_size = self.font_size
            style_height = int(float(style_height.replace("rem", "")) * font_size)
        elif style_height.endswith("em"):
            font_size = self.font_size
            style_height = int(float(style_height.replace("em", "")) * font_size)
        return int(style_height)

    def calculate_size(self) -> None:
        height = self.calculate_height()
        self.calculated_height = height
        self.height = height
        width = self.calculate_width()
        self.width = width

    def layout(self) -> None:
        super().layout()
        try:
            image = Image.open(BytesIO(self.image_bytes))
        except UnidentifiedImageError as e:
            log(f"Image is not supported: Image path {self.node.attributes.get('src')}")
            image = Image.open('resources/images/not_allowed.jpg')
        self.calculate_size()
        log("height/width", self.height, self.width)
        # TODO: Height/width can be 0 which causes problem while resizing hence workaround below.
        if self.width == 0:
            self.width = 1
        if self.height == 0:
            self.height = 1
        print("before image resize")
        image = image.resize((self.width, self.height))
        print("before image creation")
        self.image = ImageTk.PhotoImage(image)
        print("after image creation")

        if self.previous:
            space = 10
            self.x = self.previous.x + space + self.previous.width
        else:
            self.x = self.parent.x

        self.y = self.parent.y

    def paint(self, display_list: list) -> None:
        display_list.append(DrawImage(self.x, self.y, self.height, self.image))
