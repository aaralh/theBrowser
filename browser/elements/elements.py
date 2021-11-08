from tkinter import Canvas
from typing import List
from PIL import ImageTk
from browser.globals import EMOJIS_PATH
from tkinter.font import Font


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

    def execute(self, scroll: int, canvas: Canvas, supported_emojis: List[str]):
        canvas.create_rectangle(
            self.left, self.top - scroll,
            self.right, self.bottom - scroll,
            width=0,
            fill=self.color,
        )
