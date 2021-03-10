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
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT
        )
        self.activeCanvas = self.canvas
        self.canvas.pack()

    def load(self, url) -> str:
        headers = {
            "User-Agent": "theBrowser/0.01-alpha"
        }
        response = requests.get(url, headers=headers)
        return response.text

    def parseStyle(self, styleStr: str):
        styleDict = {}
        items = styleStr.split(";")
        for item in items:
            if not item:
                continue
            keyVal = item.split(":")
            styleDict[keyVal[0].strip()] = keyVal[1].strip()

        return styleDict

    def renderElement(self, element: Element):
        for child in element.childNodes:
            if isinstance(child, Element):
                child = cast(Element, child)
                print(child.attributes)
                styleDict = self.parseStyle(child.attributes.get("style", ""))
                print("styleDict")
                print(styleDict)
                if styleDict:
                    height = styleDict.get("height", 30).replace("px", "")
                    # height = ''.join([i for i in height if i.isalpha()])
                    width = styleDict.get("width", 60).replace("px", "")
                    # width = ''.join([i for i in width if i.isalpha()])
                    print(height)
                    print(width)
                    self.activeCanvas.create_rectangle(10, 20, width, height, outline="red")

            elif isinstance(child, Text):
                child = cast(Text, child)
                self.canvas.create_text(200, 150, text=child.wholeText)

            self.renderElement(child)

    def renderDOM(self, dom: DocumentType):
        for child in dom.childNodes:
            print("Child")
            print(child)
            print()
            for element in child.childNodes:
                if isinstance(element, HTMLBodyElement):
                    self.renderElement(element)

    def renderHtml(self, html: str):
        parser = HTMLDocumentParser(html)
        parser.run(self.renderDOM)


if __name__ == "__main__":
    import sys
    browser = Browser()
    html = browser.load(sys.argv[1])
    browser.renderHtml(html)
    tkinter.mainloop()
