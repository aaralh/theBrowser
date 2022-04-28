from tkinter import Canvas
from turtle import color
from typing import List
from PIL import ImageTk, Image
from browser.globals import EMOJIS_PATH
from tkinter.font import Font


def is_valid_color(color: str) -> bool:
    if color.startswith("#"):
        if not 3 < len(color) < 8:
            print("Faulty color", color)
        return 3 < len(color) < 8
    return True

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
        if self.color == "inherit" or not is_valid_color(self.color):
            self.color = "pink"
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
    
class DrawRect:
    def __init__(self, x1, y1, x2, y2, color):
        self.top = y1
        self.left = x1
        self.bottom = y2
        self.right = x2
        self.color = color
        self.used_resources = None

    def execute(self, scroll: int, canvas: Canvas, supported_emojis: List[str]):
        # TODO: Do proper implementation for rgb and rgba colors.
        if self.color == "inherit" or is_valid_color(self.color):
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
                print("fill", fill)
                print("size", (int(self.right-self.left), int(self.bottom-self.top)))
                print("position", self.left, self.top - scroll)
                image = Image.new('RGBA', (int(self.right-self.left), int(self.bottom-self.top)), fill)
                print("image", image.height, image.width)
                tk_image = ImageTk.PhotoImage(image)
                self.used_resources = tk_image
                print(self.left, self.top - scroll)
            canvas.create_image((self.left, self.top - scroll), image=self.used_resources, anchor='nw')
        else:
            canvas.create_rectangle(
                self.left, self.top - scroll,
                self.right, self.bottom - scroll,
                width=0,
                fill=self.color,
            )
