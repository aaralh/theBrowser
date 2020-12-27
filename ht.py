from web.html.parser.HTMLDocumentParser import HTMLDocumentParser
from web.html.parser.HTMLToken import HTMLToken
from web.html.parser.HTMLTokenizer import  HTMLTokenizer
import datetime

if __name__ == "__main__":
	print(datetime.datetime.now())
	with open("simple.html", "r") as htmlFile:
		html = htmlFile.read()
	parser = HTMLDocumentParser(html)
	parser.run()
	print(datetime.datetime.now())
