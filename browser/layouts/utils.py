from tkinter.font import Font
from typing import Literal, Union, cast

FONTS = {}

def font_weight_to_string(weight: Union[Literal['normal', 'bold'], str]) -> Literal['normal', 'bold']:
    if weight.isdecimal():
        if int(weight) > 500:
            return "bold"
        return "normal"
    elif weight == "bolder":
        weight = "bold"
    if not weight in ["normal", "bold"]:
        # TODO: Override all unsupported font weight values.
        weight = "normal"
    return cast(Literal['normal', 'bold'], weight)


def get_font(size: int, weight: Literal['normal', 'bold'], slant: Literal['roman', 'italic']) -> Font:
    """
    key = (size, weight, slant)
    print("Key: ", key, len(FONTS.keys()))
    if key not in FONTS:
        font = Font(size=size, weight=weight, slant=slant)
        FONTS[key] = font
    return FONTS[key]
    """
    return Font(size=size, weight=weight, slant=slant)
