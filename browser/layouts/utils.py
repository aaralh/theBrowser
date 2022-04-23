from tkinter.font import Font
from typing import Literal, Union, cast

FONTS = {}

def font_weight_to_string(weight: Union[Literal['normal', 'bold'], str]) -> Literal['normal', 'bold']:
    if weight.isdecimal():
        if int(weight) > 500:
            return "bold"
        return "normal"
    return cast(Literal['normal', 'bold'], weight)


def get_font(size: int, weight: Literal['normal', 'bold'], slant: Literal['roman', 'italic']) -> Font:
    key = (size, weight, slant)
    if key not in FONTS:
        font = Font(size=size, weight=weight, slant=slant)
        FONTS[key] = font
    return FONTS[key]
