import unittest
from typing import Any

from web.dom.Document import Document
from web.dom.DocumentType import DocumentType
from web.dom.elements import HTMLElement, HTMLHeadElement, Text, HTMLBodyElement
from web.html.parser.HTMLDocumentParser import HTMLDocumentParser
from web.html.parser.HTMLToken import HTMLTag, HTMLToken, HTMLDoctype


def expected_dom() -> Any:
    document = Document()
    docToken = HTMLDoctype()
    docType = DocumentType(docToken, document)
    htmlToken = HTMLTag(tokenType=HTMLToken.TokenType.StartTag)
    htmlToken.name = "html"
    htmlElement = HTMLElement(token=htmlToken, document=document, parent=docType)
    docType.appendChild(htmlElement)
    headToken = HTMLTag(tokenType=HTMLToken.TokenType.StartTag)
    headToken.name = "head"
    headElement = HTMLHeadElement(token=headToken, document=document, parent=htmlElement)
    htmlElement.appendChild(headElement)
    divToken = HTMLTag(tokenType=HTMLToken.TokenType.StartTag)
    divToken.name = "div"
    divElement = HTMLHeadElement(token=divToken, document=document, parent=headElement)
    headElement.appendChild(divElement)
    textElement = Text(document=document, parent=divElement, data="This is theBrowser test page")
    divElement.appendChild(textElement)
    bodyToken = HTMLTag(tokenType=HTMLToken.TokenType.StartTag)
    bodyToken.name = "body"
    bodyElement = HTMLBodyElement(token=bodyToken, document=document, parent=htmlElement)
    htmlElement.appendChild(bodyElement)
    div2Token = HTMLTag(tokenType=HTMLToken.TokenType.StartTag)
    div2Token.name = "div"
    div2Token.attributes = {
        "style": "height: 30px; width: 60px; border: 1px solid red;",
    }
    div2Element = HTMLHeadElement(token=div2Token, document=document, parent=bodyElement)
    bodyElement.appendChild(div2Element)
    text2Element = Text(document=document, parent=div2Element, data="Hello world!")
    div2Element.appendChild(text2Element)
    return docType

class MyTestCase(unittest.TestCase):
    def test_something(self) -> None:
        self.assertEqual(True, False)

    def test_parser(self) -> None:

        def t(dom: Any) -> None:
            self.assertEqual(dom, expected_dom())

        with open("./test_resources/test_html.html", "r") as htmlFile:
            html = htmlFile.read()
        parser = HTMLDocumentParser(html)
        parser.run(t)
        self.assertEqual(True, False)


if __name__ == '__main__':
    unittest.main()

