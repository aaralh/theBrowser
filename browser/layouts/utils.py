from tkinter.font import Font

FONTS = {}

def get_font(size, weight, slant) -> Font:
    key = (size, weight, slant)
    if key not in FONTS:
        font = Font(size=size, weight=weight, slant=slant)
        FONTS[key] = font
    return FONTS[key]
