from browser.elements.elements import DrawImage
from browser.layouts.Layout import Layout
from browser.utils.utils import resolve_url
from web.dom.Node import Node
from PIL import Image, ImageTk
from io import BytesIO
import requests


class ImageLayout(Layout):
    def __init__(self, node: Node, parent: Layout, previous: Layout, current_url: str):
        self.node = node
        self.children = []
        self.parent = parent
        self.previous = previous
        self.image: ImageTk = None
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        self.font = None
        self.current_url = current_url
        self.image_bytes = self.load_image()
    
    def load_image(self):
        image_src = self.node.attributes.get("src")
        src = resolve_url(image_src, self.current_url)
        response = requests.get(src)
        return response.content

    def layout(self):
        image = Image.open(BytesIO(self.image_bytes))
        height = self.node.style.get("height")
        width = self.node.style.get("width")
        image = image.resize((100, 100))
        self.width = width if width else image.width
        self.height = height if height else image.height
        self.image = ImageTk.PhotoImage(image)
            
        if self.previous:
            space = self.previous.font.measure(" ")
            self.x = self.previous.x + space + self.previous.width
        else:
            self.x = self.parent.x
            
        self.y = self.parent.y

    def paint(self, display_list: list):
        display_list.append(DrawImage(self.x, self.y, self.height, self.image))
