import tkinter
from tkinter.constants import END
from tkinter.font import Font
from typing import List
from web.dom import elements
from web.dom.elements.Element import Element
from web.dom.DocumentType import DocumentType
from web.html.parser.HTMLDocumentParser import HTMLDocumentParser
from web.dom.elements import Text, HTMLBodyElement
import requests
from PIL import Image, ImageTk

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100
EMOJIS_PATH = "resources/emojis/"


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
        self.search_button = tkinter.Button(text="GO!", command=self.loadWebpage)
        self.search_button.grid(column=1, row=0, sticky="news")
        self.canvas = tkinter.Canvas(
            self.window, 
            width=WIDTH,
            height=HEIGHT
        )
        self.canvas.grid(column=0, row=1, columnspan=2, sticky="news")
        self.scroll = 0
        self.content_height = 0
        self.current_content = ""
        self.used_resources = []
        self.supported_emojis = self.init_emojis()
        self.window.bind("<Down>", self.scroll_down)
        self.window.bind("<Up>", self.scroll_up)
        self.window.bind("<MouseWheel>", self.handle_scroll)
        self.window.bind("<Configure>", self.handle_resize)
        self.font = Font(
            family="Times",
            weight="normal",
            size=16,
        )
        """  vbar=tkinter.Scrollbar(self.window, orient=VERTICAL)
        vbar.pack(side="right", fill="y")
        vbar.config(command=self.handle_scroll) """

    def check_key(self, event):
        # Ignore the 'Return' key
        if event.keysym == "Return":
            self.loadWebpage()
            return "break"

    def init_emojis(self) -> List[str]:
        from os import listdir
        from os.path import isfile, join
        supported_emojis = [f.strip(".png") for f in listdir(EMOJIS_PATH) if isfile(join(EMOJIS_PATH, f))]
        return supported_emojis

    def handle_resize(self, event) -> None:
        if event.widget != self.window:
            return
        global WIDTH, HEIGHT
        WIDTH = event.width
        HEIGHT = event.height
        self.layout(self.current_content)
        self.used_resources = []
        self.draw()

    def load(self, url):
        self.scroll = 0
        headers = {
            "User-Agent": "theBrowser/0.01-alpha"
        }
        response = requests.get(url, headers=headers)
        parser = HTMLDocumentParser(response.text)
        parser.run(self.raster)
    
    def loadWebpage(self) -> None:
        url = self.search_bar.get("1.0", END)
        self.load(url.strip())

    def raster(self, dom: DocumentType):
        elements = lex_next_gen(get_body(dom))
        self.current_content = elements
        self.layout(elements)
        self.draw()

    def handle_scroll(self, direction):
        if direction:
            self.scroll_down(direction)
        else:
            self.scroll_up(direction)

    def scroll_down(self, _):
        if self.scroll >= self.content_height - HEIGHT:
            return
        
        if self.scroll + SCROLL_STEP >= self.content_height - HEIGHT:
            self.scroll =  self.content_height - HEIGHT
        else:
            self.scroll += SCROLL_STEP
        
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

    def layout(self, elements: List[Element]):
        self.display_list = []
        cursor_x, cursor_y = HSTEP, VSTEP
        for element in elements:
            if isinstance(element, Text):
                for word in element.data.split():
                    w = self.font.measure(word)
                    if cursor_x + w >= WIDTH - HSTEP:
                        cursor_y += self.font.metrics("linespace") * 1.2
                        cursor_x = HSTEP
                    self.display_list.append((cursor_x, cursor_y, word))
                    cursor_x += w + self.font.measure(" ")

    def draw(self):
        self.canvas.delete("all")
        for x, y, word in self.display_list:
            if y > self.scroll + HEIGHT: continue
            if y + VSTEP < self.scroll: continue
            
            if not set(list(word)).isdisjoint(set(self.supported_emojis)):
                self.canvas.create_text(x, y - self.scroll, text=word, font=self.font, anchor='nw')
            else:
                for c in word:
                    if self.is_emoji('{:X}'.format(ord(c))):
                        img = ImageTk.PhotoImage(Image.open(f"{EMOJIS_PATH}{'{:X}'.format(ord(c))}.png").resize((16, 16)))
                        self.used_resources.append(img)
                        self.canvas.create_image(x, y - self.scroll, image=img, anchor='nw')
                    else:
                        self.canvas.create_text(x, y - self.scroll, text=c, font=self.font, anchor='nw')
                    w = self.font.measure(c)
                    x += w
                
        
        if len(self.display_list):
            self.content_height = self.display_list[-1][1]




def lex(body):
    text = ""
    in_angle = False
    for c in body:
        if c == "<":
            in_angle = True
        elif c == ">":
            in_angle = False
        elif not in_angle:
            text += c
    
    return text

def lex2(dom: DocumentType) -> str:
    for child in dom.childNodes:
        for element in child.childNodes:
            if isinstance(element, HTMLBodyElement):
               return element.get_contents()


def get_body(dom: DocumentType) -> HTMLBodyElement:
    for child in dom.childNodes:
        for element in child.childNodes:
            if isinstance(element, HTMLBodyElement):
               return element

def lex_next_gen(body: HTMLBodyElement) -> List[Element]:
    out = []
    for child in body.childNodes:
        out += parse_contents(child)
    return out



def parse_contents(element: Element) -> List[Element]:
    out = [element]
    for child in element.childNodes:
         out += parse_contents(child)
    return out

    


if __name__ == "__main__":
    import sys
    browser = Browser()
    if len(sys.argv) > 1:
        url = sys.argv[1]
        browser.load(url)
        browser.search_bar.delete(1.0, END)
        browser.search_bar.insert(END, url)
    tkinter.mainloop()


