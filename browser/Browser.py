from dataclasses import dataclass
from browser.Inspector import Inspector
from browser.layouts.DocumentLayout import DocumentLayout
from browser.layouts.InlineLayout import DOMElement
import tkinter
from tkinter.constants import END
from tkinter.font import Font
from typing import List, Literal, Optional, Tuple, cast
from browser.layouts.Layout import Layout
from browser.utils.networking import load_file, request
from web.dom.CharacterData import CharacterData
from web.dom.Node import Node
from web.dom.elements.Element import Element
from web.dom.elements.HTMLInputElement import HTMLInputElement
from web.dom.DocumentType import DocumentType
from web.html.parser.HTMLDocumentParser import HTMLDocumentParser
from web.dom.elements import HTMLBodyElement, HTMLStyleElement
from browser.globals import EMOJIS_PATH, BrowserState
from browser.styling.CSSParser import CSSParser
from browser.utils.utils import tree_to_list, resolve_url
from browser.styling.utils import style, cascade_priority
from web.dom.elements import Text
import urllib


SCROLL_STEP = 10
WIDTH = 800
HEIGHT = 600

@dataclass
class FocusObject:
    node: Node
    layout: Layout

class Browser:
    def __init__(self) -> None:
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
        self.content_frame = tkinter.Frame(
            self.window,
            width=WIDTH,
            height=HEIGHT)
        self.content_frame.grid(column=0, row=1, columnspan=2, sticky="news")
        self.canvas = tkinter.Canvas(
            self.content_frame, 
            bg="white",
        )
        self.canvas.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)
        self.scroll = 0
        self.document: DocumentLayout = None
        self.used_resources = []
        self.display_list = []
        self.re_draw_timeout: Optional[str] = None
        self.supported_emojis = self.init_emojis()
        self.focus = FocusObject(None, None)

        self.window.bind("<Down>", self.scroll_down)
        self.window.bind("<Up>", self.scroll_up)
        self.window.bind("<MouseWheel>", self.handle_scroll)
        self.window.bind("<Button-4>", self.handle_scroll_linux)
        self.window.bind("<Button-5>", self.handle_scroll_linux)
        self.window.bind("<Configure>", self.handle_resize)
        self.canvas.bind("<Button-1>", self.handle_canvas_click)
        self.window.bind("<Key>", self.handle_key)
        # Right click on mac.
        self.canvas.bind("<Button-2>", self.open_context_menu)
        # Right click on linux.
        self.canvas.bind("<Button-3>", self.open_context_menu)
        self.context_menu = tkinter.Menu(self.window, tearoff=0)
        self.context_menu.add_command(label="Inspect", command=self.init_inspector)
        self.context_menu.add_command(label="Reload", command=self.load_webpage)

        self.scrollbar = tkinter.Scrollbar(self.content_frame)
        self.scrollbar.pack( side = tkinter.RIGHT, fill = tkinter.Y )
        self.scrollbar.config(command=self.scrollbar_scroll)
        
        """  vbar=tkinter.Scrollbar(self.window, orient=VERTICAL)
        vbar.pack(side="right", fill="y")
        vbar.config(command=self.handle_scroll) """
        
        with open("./browser/styling/defaults/browser.css") as file:
            self.default_style_sheet = CSSParser(file.read()).parse()

    def check_key(self, event):
        # Ignore the 'Return' key
        if event.keysym == "Return":
            try:
                self.load_webpage()
            except:
                pass
            return "break"

    def init_emojis(self) -> List[str]:
        from os import listdir
        from os.path import isfile, join
        supported_emojis = [f.strip(".png") for f in listdir(EMOJIS_PATH) if isfile(join(EMOJIS_PATH, f))]
        return supported_emojis

    def open_context_menu(self, event: tkinter.Event) -> None:
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def init_inspector(self) -> None:
        url = self.search_bar.get("1.0", END)
        BrowserState.register_inspector(Inspector(url, self, self.document.node))

    def handle_resize(self, event: tkinter.Event) -> None:
        if event.widget != self.window:
            return
        if self.re_draw_timeout != None:
            self.window.after_cancel(self.re_draw_timeout)
            self.re_draw_timeout = None
        global WIDTH, HEIGHT
        WIDTH = event.width
        HEIGHT = event.height
        self.document.height = HEIGHT
        self.re_draw_timeout = self.window.after(10, self.redraw)

    def handle_key(self, e):
        if self.canvas != self.window.focus_get(): return
        if len(e.char) == 0: return
        if not (0x20 <= ord(e.char) < 0x7f): return

        if isinstance(self.focus.node, HTMLInputElement):
            print("Key", e.char)
            self.focus.node.attributes["value"] += e.char
            self.redraw()

    def draw_cursor(self):
       if not isinstance(self.focus.node, HTMLInputElement): return 
       w = self.focus.layout.font.measure(self.focus.node.attributes["value"])
       self.canvas.create_line(self.focus.layout.x + w, self.focus.layout.y, self.focus.layout.x + w, self.focus.layout.y + 30)

    def handle_canvas_click(self, e):
        self.canvas.focus_set()
        x, y = e.x, e.y

        y += self.scroll
        objs = [obj for obj in tree_to_list(self.document, []) if obj.x <= x < obj.x + obj.width and obj.y <= y < obj.y + obj.height]
        if not objs: return
        obj = objs[-1]
        elt = obj.node

        while elt:
            print("Element: ", elt.name)
            if isinstance(elt, Text):
                pass
            elif elt.name == "a" and "href" in elt.attributes:
                url = resolve_url(elt.attributes["href"], BrowserState.get_current_url())
                self.search_bar.delete(1.0, END)
                self.search_bar.insert(END, url)
                return self.load(url)
            elif elt.name == "input":
                if elt.attributes.get("type", "") == "submit":
                    while elt:
                        if elt.name == "form" and "action" in elt.attributes:
                            return self.submit_form(elt)
                        elt = elt.parentNode
                else:
                    print("Element:", elt)
                    elt.attributes["value"] = ""
                    self.focus = FocusObject(node=elt, layout=obj)
                    return
            elif elt.name == "button":
                while elt:
                    if elt.name == "form" and "action" in elt.attributes:
                        return self.submit_form(elt)
                    elt = elt.parentNode
            elt = elt.parentNode

    def submit_form(self, elt):
        inputs = [node for node in tree_to_list(elt, [])
                  if isinstance(node, Element)
                  and node.name == "input"
                  and "name" in node.attributes]
        
        body = ""
        for input in inputs:
            name = input.attributes["name"]
            value = input.attributes.get("value", "")
            name = urllib.parse.quote(name)
            value = urllib.parse.quote(value)
            body += "&" + name + "=" + value
        body = body[1:]
        url = resolve_url(elt.attributes["action"] + f"?{body}", BrowserState.get_current_url())
        self.search_bar.delete(1.0, END)
        self.search_bar.insert(END, url)
        self.load(url)

    def redraw(self) -> None:
        self.re_draw_timeout = None
        if self.document:
            self.document.layout(WIDTH)
            self.display_list = []
            self.document.paint(self.display_list)
        self.used_resources = []
        self.draw_cursor()
        self.draw()

    def load(self, url: str, body=None):
        self.scroll = 0
        BrowserState.set_current_url(url)
        [inspector.update_url(url) for inspector in BrowserState.get_inspectors()]
        [inspector.clear_network_requests() for inspector in BrowserState.get_inspectors()]
        if url.startswith("file://"):
            response = load_file(url)
        else: 
            response = request(url).text
        parser = HTMLDocumentParser(response)
        parser.run(self.raster)
    
    def load_webpage(self) -> None:
        url = self.search_bar.get("1.0", END)
        self.load(url.strip())

    def raster(self, dom: DocumentType):
        rules = self.default_style_sheet.copy()

        stylesheet_links = [node.attributes["href"]
             for node in tree_to_list(dom, [])
             if isinstance(node, Element)
             and node.name == "link"
             and "href" in node.attributes
             and node.attributes.get("rel") == "stylesheet"]
        for link in stylesheet_links:
            try:
                response = request(resolve_url(link, BrowserState.get_current_url()))
            except Exception as e:
                continue
            rules.extend(CSSParser(response.text).parse())
        style_elements = [node for node in tree_to_list(dom, []) if isinstance(node, HTMLStyleElement)]
        for style_element in style_elements:
            for child in style_element.children:
                child = cast(CharacterData, child)
                rules.extend(CSSParser(child.data).parse())

        with open("rules.txt", "w") as f:
            for rule in rules:
                f.write(str(rule.__dict__) + "\n")
        style(dom, sorted(rules, key=cascade_priority))
        with open("document.html", "w") as f:
            f.write(str(dom))
        self.document = DocumentLayout(dom)
        [inspector.update_dom(dom) for inspector in BrowserState.get_inspectors()]
        self.document.height = HEIGHT
        self.document.layout(WIDTH)
        self.scrollbar.set((self.scroll/self.document.content_height), ((self.scroll + HEIGHT)/self.document.content_height)) 
        self.display_list = []
        self.document.paint(self.display_list)
            
        self.draw()

    def handle_scroll_linux(self, event: tkinter.Event):
        if event.num == 5:
            self.scroll_down(-1)
        elif event.num == 4:
            self.scroll_up(1)



    def handle_scroll(self, direction: tkinter.Event):
        if direction.delta < 0:
            self.scroll_down(direction.delta)
        else:
            self.scroll_up(direction.delta)

    def scroll_down(self, delta: int):
        delta = delta * -1
        max_y = (self.document.content_height - HEIGHT) + 15
        scroll = min(self.scroll + (delta * SCROLL_STEP), max_y)
        if scroll <= 0:
            self.scroll = 0
        else:
            self.scroll = scroll
        print((self.scroll/self.document.content_height), ((self.scroll + HEIGHT)/self.document.content_height))
        self.scrollbar.set((self.scroll/self.document.content_height), ((self.scroll + HEIGHT)/self.document.content_height))
        self.draw()

    def scroll_up(self, delta):
        if self.scroll <= 0:
            self.scroll = 0
            self.draw()
            return

        if self.scroll - (delta * SCROLL_STEP) <= 0:
            self.scroll = 0
        else:
            self.scroll -= (delta * SCROLL_STEP)
        print((self.scroll/self.document.content_height), ((self.scroll + HEIGHT)/self.document.content_height))
        self.scrollbar.set((self.scroll/self.document.content_height), ((self.scroll + HEIGHT)/self.document.content_height))
        self.draw()

    def scrollbar_scroll(self, action: Literal["moveto"], position: str):
        position_float = float(position)
        print(position,  not 0 <= position_float <= 1)
        if not 0 <= position_float <= 1:
            return
        print(0 <= position_float <= 1)
        self.scroll = self.document.content_height * position_float
        self.scrollbar.set((self.scroll/self.document.content_height), ((self.scroll + HEIGHT)/self.document.content_height))
        self.draw()

    def is_emoji(self, unicode) -> bool:
        return unicode in self.supported_emojis

    def draw(self) -> None:
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
    for child in body.children:
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
    for child in element.children:
         out += parse_contents(child, _font)
    return out
