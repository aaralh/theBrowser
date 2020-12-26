from web.html.parser.HTMLDocumentParser import HTMLDocumentParser
from web.html.parser.HTMLToken import HTMLToken
from web.html.parser.HTMLTokenizer import  HTMLTokenizer

if __name__ == "__main__":
	with open("google_frontpage.html", "r") as htmlFile:
		html = htmlFile.read()
	print(html)
	parser = HTMLDocumentParser(html)
	parser.run()