from dataclasses import dataclass
from tkinter import Canvas
from typing import List, cast
from PIL import ImageTk, Image
from tkinter.font import Font
from typing import NewType

from browser.styling.color.utils import ValidColor, rgba_to_hex, transform_color

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
        self.calculated_color = None

    def is_emoji(self, unicode, supported_emojis: List[str]) -> bool:
        return unicode in supported_emojis

    def execute(self, scroll: int, canvas: Canvas, supported_emojis: List[str]):
        if not self.calculated_color:
            self.calculated_color = transform_color(self.color)
        color = self.calculated_color.color
        if self.calculated_color.type == "rgba_color":
            color = "#" + rgba_to_hex(color)[:-2]
        canvas.create_text(self.left, self.top - scroll, text=self.text, font=self.font, anchor='nw', fill=color)
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
    color: ValidColor
    width: int

class DrawRect:
    def __init__(self, x1, y1, x2, y2, color: ValidColor, border: BorderProperties = BorderProperties(transform_color(""), 0)):
        self.top = y1
        self.left = x1
        self.bottom = y2
        self.right = x2
        self.color = color
        self.used_resources = None
        self.border = border

    def execute(self, scroll: int, canvas: Canvas, supported_emojis: List[str]):
        # TODO: Do proper implementation for rgb and rgba colors.
        if self.color.type == "rgba_color":
            if not self.used_resources:
                image = Image.new('RGBA', (int(self.right-self.left), int(self.bottom-self.top)), self.color.color)
                tk_image = ImageTk.PhotoImage(image)
                self.used_resources = tk_image
            canvas.create_image((self.left, self.top - scroll), image=self.used_resources, anchor='nw')
        if not self.color.type == "rgba_color":
            outline = self.border.color.color
            if self.border.color.type == "rgba_color":
                outline = "#" + rgba_to_hex(outline)[:-2]
            canvas.create_rectangle(
                self.left, self.top - scroll,
                self.right, self.bottom - scroll,
                width=self.border.width,
                fill=self.color.color,
                outline=outline
            )
