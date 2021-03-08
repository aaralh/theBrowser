import tkinter
import requests
from web.html.parser.HTMLDocumentParser import HTMLDocumentParser

WIDTH, HEIGHT = 800, 600


class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT
        )
        self.canvas.pack()

    def load(self, url) -> str:
        headers = {
            "User-Agent": "theBrowser/0.01-alpha"
        }
        response = requests.get(url, headers=headers)
        return response.text

    def renderDOM(self, dom):
        print(dom)
        self.canvas.create_rectangle(10, 20, 400, 300, tags="playbutton")
        self.canvas.create_oval(100, 100, 150, 150)
        self.canvas.create_text(200, 150, text="Hi!")

    def renderHtml(self, html: str):
        parser = HTMLDocumentParser(html)
        parser.run(self.renderDOM)


if __name__ == "__main__":
    import sys
    browser = Browser()
    html = browser.load(sys.argv[1])
    browser.renderHtml(html)
    tkinter.mainloop()
