from dataclasses import dataclass
from tkinter import Canvas
from turtle import color
from typing import List, cast
from PIL import ImageTk, Image
from browser.globals import EMOJIS_PATH
from tkinter.font import Font


def is_valid_color(color: str) -> bool:
    if color.startswith("#") and any(char in color for char in [" ", ";", ","]):
        return False
        
    if color.startswith("#"):
        # TODO: Add support for rgba style hex colors.
        if not len(color[1:]) in [3, 6]:
            print("Faulty color", color)
        return len(color[1:]) in [3, 6]
    return True

def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return '%02x%02x%02x' % rgb

class DrawImage:
    def __init__(self, x1, y1, height, image: ImageTk):
        self.top = y1
        self.left = x1
        self.image = image
        self.bottom = y1 + height
        self.used_resources = []

    def execute(self, scroll: int, canvas: Canvas, supported_emojis: List[str]):
        canvas.create_image(self.left, self.top - scroll, image=self.image, anchor='nw')


class DrawText:
    def __init__(self, x1, y1, text: str, font: Font, color):
        self.top = y1
        self.left = x1
        self.text = text
        self.font = font
        self.color = color
        self.bottom = y1 + font.metrics("linespace")
        self.used_resources = []

    def is_emoji(self, unicode, supported_emojis: List[str]) -> bool:
        return unicode in supported_emojis

    def execute(self, scroll: int, canvas: Canvas, supported_emojis: List[str]):
        # TODO: Do proper implementation for rgb and rgba colors.
        if self.color == "inherit" or self.color == "transparent" or self.color.startswith("var") or not is_valid_color(self.color):
            self.color = "pink"
        
        if self.color.startswith("rgb"):
            # TODO: Add support for rgba
            rgb = cast(tuple[int, int, int], tuple([int(number) for number in self.color.split("(")[-1].split(")")[0].split(",")[:3]]))
            self.color = "#" + rgb_to_hex(rgb)

        canvas.create_text(self.left, self.top - scroll, text=self.text, font=self.font, anchor='nw', fill=self.color)
        """if not set(list(self.text)).isdisjoint(set(supported_emojis)):
            canvas.create_text(self.left, self.top - scroll, text=self.text, font=self.font, anchor='nw', fill=self.color)
        else:
            tmp_left = self.left
            for c in self.text:
                if self.is_emoji('{:X}'.format(ord(c)), supported_emojis):
                    img = ImageTk.PhotoImage(Image.open(f"{EMOJIS_PATH}{'{:X}'.format(ord(c))}.png").resize((16, 16)))
                    self.used_resources.append(img)
                    canvas.create_image(tmp_left, self.top - scroll, image=img, anchor='nw')
                else:
                    canvas.create_text(tmp_left, self.top - scroll, text=c, font=self.font, anchor='nw', fill=self.color)
                w = self.font.measure(c)
                tmp_left += w"""


@dataclass
class BorderProperties:
    color: str
    width: int


class DrawRect:
    def __init__(self, x1, y1, x2, y2, color, border: BorderProperties = BorderProperties("", 0)):
        self.top = y1
        self.left = x1
        self.bottom = y2
        self.right = x2
        self.color = color
        self.used_resources = None
        self.border = border

    def execute(self, scroll: int, canvas: Canvas, supported_emojis: List[str]):
        # TODO: Do proper implementation for rgb and rgba colors.
        if self.color == "inherit" or self.color.startswith("var") or not is_valid_color(self.color):
            self.color = "pink"
        
        if self.color.startswith("rgba"):
            if not self.used_resources:
                if ", " in self.color:
                    rgba = [float(value) for value in self.color[5:-1].split(", ")]
                else:
                    rgba = [float(value) for value in self.color[5:-1].split(",")]
                rgba[3] = 255 * rgba[3]
                rgba = [int(value) for value in rgba]
                fill = tuple(rgba)
                image = Image.new('RGBA', (int(self.right-self.left), int(self.bottom-self.top)), fill)
                tk_image = ImageTk.PhotoImage(image)
                self.used_resources = tk_image
            canvas.create_image((self.left, self.top - scroll), image=self.used_resources, anchor='nw')
        elif self.color.startswith("rgb"):
            rgb = cast(tuple[int, int, int], tuple([int(number) for number in self.color.split("(")[-1].split(")")[0].split(",")[:3]]))
            self.color = "#" + rgb_to_hex(rgb)
        if not self.color.startswith("rgba"):
            if self.color == "none": self.color = "pink"
            canvas.create_rectangle(
                self.left, self.top - scroll,
                self.right, self.bottom - scroll,
                width=self.border.width,
                fill=self.color,
                outline=self.border.color
            )
