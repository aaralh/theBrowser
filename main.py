import tkinter
from tkinter.constants import LEFT
import requests

from web.dom.Node import Node
from web.dom.elements import Text, HTMLBodyElement
from web.dom.elements.Element import Element
from web.html.parser.HTMLDocumentParser import HTMLDocumentParser
from web.dom.DocumentType import DocumentType
from time import sleep

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
        self.main_frame = tkinter.Frame(self.window, padx=0, pady=0)
        self.active_element = self.main_frame
        self.main_frame.grid(column=0, row=1)

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

                    row, _ = _active_element.grid_size()
                    _active_element = tkinter.Frame(
                        _active_element,
                       """  height=height,
                        width=width,
                        highlightbackground=border_color,
                        highlightthickness=border_width """)
                    _active_element.grid(column=0, row=counter)# type: ignore
                    counter = 0

            elif isinstance(child, Text):
                child = cast(Text, child)
                row, _ = _active_element.grid_size()
                text_widget = tkinter.Label(_active_element, text=child.data, justify=LEFT, wraplength=800)  # type: ignore
                text_widget.grid(column=0, row=counter)
            
            if not isinstance(child, Text):
                self.renderElement(child, _active_element, counter)
                
            counter = counter + 1


    def renderDOM(self, dom: DocumentType) -> None:
        print("dom")
        print(dom)
        for child in dom.childNodes:
            print("Child")
            print(child)
            print()
            for element in child.childNodes:
                if isinstance(element, HTMLBodyElement):
                    self.renderElement(element, self.active_element, 0)

    def renderHtml(self, html: str) -> None:
        parser = HTMLDocumentParser(html)
        parser.run(self.renderDOM)


if __name__ == "__main__":
    import sys
    browser = Browser()

    if sys.argv[1]:
        html = browser.load(sys.argv[1])
    else:
        with open("./test_resources/test_html.html", "r") as htmlFile:
            html = htmlFile.read()
    browser.renderHtml(html)

    tkinter.mainloop()

