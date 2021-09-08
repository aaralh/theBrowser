import tkinter
from tkinter.constants import END, LEFT
import requests

from web.dom.Node import Node
from web.dom.elements import Text, HTMLBodyElement
from web.dom.elements.Element import Element
from web.html.parser.HTMLDocumentParser import HTMLDocumentParser
from web.dom.DocumentType import DocumentType
from time import sleep
from widgets.ScrollableFrame import ScrollableFrame

from typing import cast
""" import os

if os.environ.get('DISPLAY','') == '':
    print('no display found. Using :0')
    os.environ.__setitem__('DISPLAY', ':0') """

WIDTH, HEIGHT = 800, 600


class Browser:
    def __init__(self) -> None:
        self.window = tkinter.Tk(className='theBrowser')
        self.window.geometry(f"{WIDTH}x{HEIGHT}")
        self.search_bar = tkinter.Text(self.window, height=1)
        self.search_bar.grid(column=0, row=1)
        self.search_bar.bind("<Key>", self.check_key)
        self.search_button = tkinter.Button(text="GO!", command=self.loadWebpage)
        self.search_button.grid(column=1, row=1)
        self.test = tkinter.Frame(self.window, height=60, width=60, bd=2)
        self.test.grid(column=0, row=2)
        self.scrollable_frame = ScrollableFrame(self.test)
        self.scrollable_frame.grid(column=0, row=1)
        self.main_frame = tkinter.Frame(self.scrollable_frame.scrollable_frame)
        self.main_frame.grid(column=0, row=0)
        self.active_element = self.main_frame

    def check_key(self, event):
        # Ignore the 'Return' key
        if event.keysym == "Return":
            self.loadWebpage()
            return "break"

    def load(self, url: str) -> str:
        headers = {
            "User-Agent": "theBrowser/0.01-alpha"
        }
        response = requests.get(url, headers=headers)
        return response.text

    def parseStyle(self, styleStr: str) -> dict:
        styleDict = {}
        items = styleStr.split(";")
        for item in items:
            if not item:
                continue
            keyVal = item.split(":")
            styleDict[keyVal[0].strip()] = keyVal[1].strip()

        return styleDict

    def renderElement(self, element: Element, active_element: tkinter.Frame, counter: int) -> None:
        _active_element = active_element
        for child in element.childNodes:
            print("child: ", child)
            if isinstance(child, Element):
                child = cast(Element, child)
                style_dict = self.parseStyle(child.attributes.get("style", ""))
                if style_dict:
                    height = style_dict.get("height", "0").replace("px", "")
                    # height = ''.join([i for i in height if i.isalpha()])
                    width = style_dict.get("width", "0").replace("px", "")
                    border_color = style_dict.get("border-color", "")
                    border_width = style_dict.get("border-width", "").replace("px", "")
                    # width = ''.join([i for i in width if i.isalpha()])

                    e = tkinter.Frame(_active_element)
                    e.grid(column=0, row=counter)# type: ignore
                    self.renderElement(child, e, 1)


            elif isinstance(child, Text):
                child = cast(Text, child)
                if child.data.isspace():
                    continue
                text_widget = tkinter.Label(_active_element, text=child.data, justify=LEFT, wraplength=800)  # type: ignore
                text_widget.grid(column=0, row=counter)
            
            if not isinstance(child, Text):
                self.renderElement(child, _active_element, counter)
                
            counter = counter + 1


    def renderDOM(self, dom: DocumentType) -> None:
        for child in dom.childNodes:
            for element in child.childNodes:
                if isinstance(element, HTMLBodyElement):
                    self.renderElement(element, self.active_element, 1)

    def renderHtml(self, html: str) -> None:
        parser = HTMLDocumentParser(html)
        parser.run(self.renderDOM)

    def loadWebpage(self) -> None:
        url = self.search_bar.get("1.0", END)
        html = self.load(url.strip())
        for child in self.main_frame.winfo_children():
             child.destroy()
        self.active_element = self.main_frame
        self.renderHtml(html)



if __name__ == "__main__":
    import sys
    browser = Browser()

    if len(sys.argv) > 1:
        url = sys.argv[1]
        html = browser.load(url)
        browser.search_bar.delete(1.0, END)
        browser.search_bar.insert(END, url)
        browser.renderHtml(html)

    tkinter.mainloop()

