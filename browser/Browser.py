from browser.layouts.DocumentLayout import DocumentLayout
from browser.layouts.InlineLayout import DOMElement
import tkinter
from tkinter.constants import END
from tkinter.font import Font
from typing import List, Tuple
from web.dom.elements.Element import Element
from web.dom.DocumentType import DocumentType
from web.html.parser.HTMLDocumentParser import HTMLDocumentParser
from web.dom.elements import HTMLBodyElement
import requests
from PIL import Image, ImageTk
import browser.globals as globals
from browser.globals import EMOJIS_PATH

SCROLL_STEP = 100
WIDTH = 800
HEIGHT = 600

class Browser:
    def __init__(self):
        self.window = tkinter.Tk(className='theBrowser')
        self.window.rowconfigure(0, weight=1)
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(1, weight=1000)
        self.window.columnconfigure(1, weight=1)
        self.search_bar = tkinter.Text(self.window, height=1)
        self.search_bar.grid(column=0, row=0, sticky="news")
        self.search_bar.bind("<Key>", self.check_key)
        self.search_button = tkinter.Button(text="GO!", command=self.load_webpage)
        self.search_button.grid(column=1, row=0, sticky="news")
        self.canvas = tkinter.Canvas(
            self.window, 
            width=WIDTH,
            height=HEIGHT
        )
        self.canvas.grid(column=0, row=1, columnspan=2, sticky="news")
        self.scroll = 0
        self.content_height = 0
        self.document: DocumentLayout = None
        self.used_resources = []
        self.display_list = []
        self.re_draw_timeout = None
        self.supported_emojis = self.init_emojis()
        self.window.bind("<Down>", self.scroll_down)
        self.window.bind("<Up>", self.scroll_up)
        self.window.bind("<MouseWheel>", self.handle_scroll)
        self.window.bind("<Configure>", self.handle_resize)
        """  vbar=tkinter.Scrollbar(self.window, orient=VERTICAL)
        vbar.pack(side="right", fill="y")
        vbar.config(command=self.handle_scroll) """

    def check_key(self, event):
        # Ignore the 'Return' key
        if event.keysym == "Return":
            self.load_webpage()
            return "break"

    def init_emojis(self) -> List[str]:
        from os import listdir
        from os.path import isfile, join
        supported_emojis = [f.strip(".png") for f in listdir(EMOJIS_PATH) if isfile(join(EMOJIS_PATH, f))]
        return supported_emojis

    def handle_resize(self, event) -> None:
        if event.widget != self.window:
            return
        if self.re_draw_timeout != None:
            self.window.after_cancel(self.re_draw_timeout)
            self.re_draw_timeout = None
        global WIDTH, HEIGHT
        WIDTH = event.width
        HEIGHT = event.height
        self.re_draw_timeout = self.window.after(10, self.redraw)
        
    def redraw(self) -> None:
        self.re_draw_timeout = None
        self.document.layout(WIDTH)
        self.display_list = []
        self.document.paint(self.display_list)
        self.used_resources = []
        self.draw()

    def load(self, url):
        self.scroll = 0
        headers = {
            "User-Agent": "theBrowser/0.02-alpha"
        }
        response = requests.get(url, headers=headers)
        parser = HTMLDocumentParser(response.text)
        parser.run(self.raster)
    
    def load_webpage(self) -> None:
        url = self.search_bar.get("1.0", END)
        self.load(url.strip())

    def raster(self, dom: DocumentType):
        self.document = DocumentLayout(dom)
        self.document.layout(WIDTH)
        self.display_list = []
        self.document.paint(self.display_list)
        self.draw()

    def handle_scroll(self, direction):
        if direction:
            self.scroll_down(direction)
        else:
            self.scroll_up(direction)

    def scroll_down(self, _):
        max_y = self.document.height - HEIGHT
        self.scroll = min(self.scroll + SCROLL_STEP, max_y)
        self.draw()

    def scroll_up(self, _):
        if self.scroll <= 0:
            return

        if self.scroll - SCROLL_STEP <= 0:
            self.scroll = 0
        else:
            self.scroll -= SCROLL_STEP
        
        self.draw()

    def is_emoji(self, unicode) -> bool:
        return unicode in self.supported_emojis


    def draw(self):
        self.canvas.delete("all")
        for cmd in self.display_list:
            if cmd.top > self.scroll + HEIGHT: continue
            if cmd.bottom < self.scroll: continue
            cmd.execute(self.scroll, self.canvas, self.supported_emojis)
        """ for x, y, word, font in self.display_list:
            if y > self.scroll + globals.HEIGHT: continue
            if y + globals.VSTEP < self.scroll: continue
            
            if not set(list(word)).isdisjoint(set(self.supported_emojis)):
                self.canvas.create_text(x, y - self.scroll, text=word, font=font, anchor='nw')
            else:
                for c in word:
                    if self.is_emoji('{:X}'.format(ord(c))):
                        img = ImageTk.PhotoImage(Image.open(f"{EMOJIS_PATH}{'{:X}'.format(ord(c))}.png").resize((16, 16)))
                        self.used_resources.append(img)
                        self.canvas.create_image(x, y - self.scroll, image=img, anchor='nw')
                    else:
                        self.canvas.create_text(x, y - self.scroll, text=c, font=font, anchor='nw')
                    w = font.measure(c)
                    x += w """
                


def lex_next_gen(body: HTMLBodyElement) -> List[DOMElement]:
    out = []
    weight = "normal"
    style = "roman"
    font = Font(
        size=16,
        weight=weight,
        slant=style,
    )
    for child in body.childNodes:
        out += parse_contents(child, font)
    return out

def get_font_weight_and_style(element: Element) -> Tuple:
    style = None
    weight = None

    if element.name == "i":
        style = "italic"
    elif element.name == "b" or element.name == "strong":
        weight = "bold"

    return (style, weight)

def parse_contents(element: Element, font: Font) -> List[DOMElement]:
    _font = font.copy()
    out = [DOMElement(element, _font)]
    style, weight = get_font_weight_and_style(element)
    if style:
        _font.config(style=style)
    if weight:
        _font.config(weight=weight)
    for child in element.childNodes:
         out += parse_contents(child, _font)
    return out