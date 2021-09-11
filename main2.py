import tkinter
from tkinter.constants import RIGHT, VERTICAL, Y
from web.dom.DocumentType import DocumentType
from web.html.parser.HTMLDocumentParser import HTMLDocumentParser
from web.dom.elements import Text, HTMLBodyElement
import requests
WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100

class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window, 
            width=WIDTH,
            height=HEIGHT
        )
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scroll = 0
        self.content_height = 0
        self.current_content = ""
        self.window.bind("<Down>", self.scroll_down)
        self.window.bind("<Up>", self.scroll_up)
        self.window.bind("<MouseWheel>", self.handle_scroll)
        self.window.bind("<Configure>", self.handle_resize)
        vbar=tkinter.Scrollbar(self.window, orient=VERTICAL)
        vbar.pack(side="right", fill="y")
        vbar.config(command=self.handle_scroll)

    def handle_resize(self, event) -> None:
        global WIDTH, HEIGHT
        WIDTH = event.width
        HEIGHT = event.height
        self.canvas.config(height=HEIGHT, width=WIDTH)
        self.display_list = layout(self.current_content)
        self.draw()

    def load(self, url):
        headers = {
            "User-Agent": "theBrowser/0.01-alpha"
        }
        response = requests.get(url, headers=headers)
        parser = HTMLDocumentParser(response.text)
        parser.run(self.raster)
       

    def raster(self, dom: DocumentType):
        text = lex(lex2(dom))
        self.current_content = text
        self.display_list = layout(text)
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

    def draw(self):
        self.canvas.delete("all")
        for x, y, c in self.display_list:
            if y > self.scroll + HEIGHT: continue
            if y + VSTEP < self.scroll: continue
            self.canvas.create_text(x, y - self.scroll, text=c)
            
        self.content_height = self.display_list[-1][1]


def layout(text: str):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    for c in text:
        if c == "\n":
            cursor_y += VSTEP
            cursor_x = HSTEP
            continue
        display_list.append((cursor_x, cursor_y, c))
        cursor_x += HSTEP
        if cursor_x >= WIDTH - HSTEP:
            cursor_y += VSTEP
            cursor_x = HSTEP
    return display_list

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

if __name__ == "__main__":
    import sys
    Browser().load(sys.argv[1])
    tkinter.mainloop()