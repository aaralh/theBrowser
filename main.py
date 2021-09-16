from browser.Browser import Browser
import tkinter
from tkinter.constants import END

if __name__ == "__main__":
    import sys
    browser = Browser()
    if len(sys.argv) > 1:
        url = sys.argv[1]
        browser.load(url)
        browser.search_bar.delete(1.0, END)
        browser.search_bar.insert(END, url)
    tkinter.mainloop()


