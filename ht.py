from web.HTMLDocumentParser import HTMLDocumentParser
from web.HTMLToken import HTMLToken
from web.HTMLTokenizer import  HTMLTokenizer

if __name__ == "__main__":
	with open("simple.html", "r") as htmlFile:
		html = htmlFile.read()
	print(html)

	parser = HTMLDocumentParser(html)
	parser.run()