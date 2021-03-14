from typing import Any

from web.html.parser.HTMLDocumentParser import HTMLDocumentParser
from web.html.parser.HTMLToken import HTMLToken
from web.html.parser.HTMLTokenizer import  HTMLTokenizer
import datetime


def cb(dom: Any) -> None:
	print(dom)


if __name__ == "__main__":
	print(datetime.datetime.now())
	with open("./test_resources/test_html.html", "r") as htmlFile:
		html = htmlFile.read()
	parser = HTMLDocumentParser(html)
	parser.run(cb)
	print(datetime.datetime.now())
