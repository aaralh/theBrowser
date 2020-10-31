from web.HTMLToken import HTMLToken
from web.HTMLTokenizer import  HTMLTokenizer

if __name__ == "__main__":
	with open("simple.html", "r") as htmlFile:
		html = htmlFile.read()
	print(html)

	tokenizer = HTMLTokenizer(html)
	tokenizer.run()