import tkinter
import requests

from web.dom.Node import Node
from web.dom.elements import Text, HTMLBodyElement
from web.dom.elements.Element import Element
from web.html.parser.HTMLDocumentParser import HTMLDocumentParser
from web.dom.DocumentType import DocumentType

from typing import cast

WIDTH, HEIGHT = 800, 600


class Browser:
    def __init__(self) -> None:
        self.window = tkinter.Tk(className='theBrowser')
        self.window.geometry(f"{WIDTH}x{HEIGHT}")
        self.main_frame = tkinter.Frame(self.window)
        self.active_element = self.main_frame
        self.main_frame.pack(side=tkinter.LEFT, anchor=tkinter.N)

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

    def renderElement(self, element: Element) -> None:
        for child in element.childNodes:
            if isinstance(child, Element):
                child = cast(Element, child)
                print(child.attributes)
                style_dict = self.parseStyle(child.attributes.get("style", ""))
                print("style_dict")
                print(style_dict)
                if style_dict:
                    height = style_dict.get("height", "0").replace("px", "")
                    # height = ''.join([i for i in height if i.isalpha()])
                    width = style_dict.get("width", "0").replace("px", "")
                    border_color = style_dict.get("border-color", "")
                    border_width = style_dict.get("border-width", "").replace("px", "")
                    # width = ''.join([i for i in width if i.isalpha()])
                    print(height)
                    print(width)
                    self.active_element = tkinter.Frame(
                        self.active_element,
                        height=height,
                        width=width,
                        highlightbackground=border_color,
                        highlightthickness=border_width)
                    self.active_element.pack(side=tkinter.LEFT, anchor=tkinter.N, pady=0, padx=0)# type: ignore

            elif isinstance(child, Text):
                child = cast(Text, child)
                text_widget = tkinter.Label(self.active_element, text=child.wholeText)  # type: ignore
                text_widget.pack(side=tkinter.LEFT, anchor=tkinter.N)

            self.renderElement(child)

    def renderDOM(self, dom: DocumentType) -> None:
        for child in dom.childNodes:
            print("Child")
            print(child)
            print()
            for element in child.childNodes:
                if isinstance(element, HTMLBodyElement):
                    self.renderElement(element)

    def renderHtml(self, html: str) -> None:
        parser = HTMLDocumentParser(html)
        parser.run(self.renderDOM)


if __name__ == "__main__":
    import sys
    browser = Browser()
    #  html = browser.load(sys.argv[1])
    with open("./test_resources/test_html.html", "r") as htmlFile:
        html = htmlFile.read()
    browser.renderHtml(html)
    tkinter.mainloop()
