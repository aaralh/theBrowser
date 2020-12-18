from enum import Enum, auto
from typing import Any, List, Union, Callable, cast
from web.html.parser.ListOfActiveElements import ListOfActiveElements
from web.html.parser.StackOfOpenElments import StackOfOpenElments
from web.dom.CharacterData import CharacterData
from web.dom.elements.Comment import Comment
from web.html.parser.utils import charIsWhitespace
from web.dom.elements.Element import Element
from web.dom.Document import Document
from web.dom.Node import Node
from web.dom.elements.Text import Text
from web.dom.DocumentType import DocumentType
from web.html.parser.HTMLToken import HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter
from web.html.parser.HTMLTokenizer import HTMLTokenizer
from web.dom.ElementFactory import ElementFactory


class HTMLDocumentParser:

    class __Mode(Enum):
        Initial = auto()
        BeforeHTML = auto()
        BeforeHead = auto()
        InHead = auto()
        InHeadNoscript = auto()
        AfterHead = auto()
        InBody = auto()
        Text = auto()
        InTable = auto()
        InTableText = auto()
        InCaption = auto()
        InColumnGroup = auto()
        InTableBody = auto()
        InRow = auto()
        InCell = auto()
        InSelect = auto()
        InSelectInTable = auto()
        InTemplate = auto()
        AfterBody = auto()
        InFrameset = auto()
        AfterFrameset = auto()
        AfterAfterBody = auto()
        AfterAfterFrameset = auto()

    def __init__(self, html: str) -> None:
        self.__currentInsertionMode = self.__Mode.Initial
        self.__originalInsertionMode: Union[self.__Mode, None] = None
        self.__openElements = StackOfOpenElments()
        self.__tokenizer = HTMLTokenizer(html, self.__tokenHandler)
        self.__document = Document()
        self.__currentElement = self.__document
        self.__scripting: bool = False
        self.__framesetOK: bool = True
        self.__formattingElements = ListOfActiveElements()

    def run(self) -> None:
        self.__tokenizer.run()

    def __getOpenElement(self) -> Node:
        '''
        Gets the latest opened element aka "parent".
        '''
        return self.__document if self.__openElements.isEmpty() else self.__openElements.last()

    def __tokenHandler(self, token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
        switcher = self.__getModeSwitcher()
        if (switcher != None):
            switcher(token)

        if (token.type == HTMLToken.TokenType.EOF):
            print("The dom")
            print(self.__document)

    def __continueIn(self, mode: __Mode) -> None:
        self.__switchModeTo(mode)

    def __switchModeTo(self, newMode: __Mode) -> None:
        '''
        Switch state and consume next character.
        '''
        self.__currentInsertionMode = newMode
        """ switcher = self.__getModeSwitcher()
        if (switcher != None):
            switcher() """

    def __reconsumeIn(self, newMode: __Mode, token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
        '''
        Switch state without consuming next character.
        '''
        self.State = newMode
        switcher = self.__getModeSwitcher()
        if (switcher != None):
            switcher(token)

    def __createElement(self, token: HTMLTag) -> Element:
        '''
        Creates element based on given token and sets parent for it.
        '''
        parent = self.__getOpenElement()
        element = ElementFactory.create_element(token, parent, parent.document)
        element.parentNode.appendChild(element)

        return element

    def __insertCharacter(self, token: HTMLCommentOrCharacter) -> None:
        if (type(self.__currentElement) is Document):
            return
        elif (len(self.__currentElement.childNodes) > 0 and type(self.__currentElement.childNodes[-1]) is Text):
            cast(
                Text, self.__currentElement.childNodes[-1]).appendData(token.data)
        else:
            textNode = Text(self.__document, self.__currentElement, token.data)
            print("self.__currentElement")
            print(self.__currentElement.name)
            textNode.parentNode = self.__currentElement
            self.__currentElement.appendChild(textNode)

    def __insertComment(self, token: HTMLCommentOrCharacter) -> None:
        comment = Comment(token.data)
        comment.parentNode = self.__currentElement
        self.__currentElement.appendChild(comment)
        self.__continueIn(self.__Mode.BeforeHead)

    def __adoptionAgencyAlgorithm(self, token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
        subject = token.name
        if (self.__currentElement.name == subject and not self.__formattingElements.contains(self.__currentElement)):
            self.__openElements.pop()
            return
        outerLoopCounter = 0

        while outerLoopCounter < 8:
            outerLoopCounter += 1
            formattingElement = self.__formattingElements.lastElementWithTagNameBeforeMarker(
                subject)

            if (not self.__elementInOpenStackScope(formattingElement)):
                self.__formattingElements.remove(formattingElement)
            # TODO: Continue here https://html.spec.whatwg.org/multipage/parsing.html#adoption-agency-algorithm
            # https://html.spec.whatwg.org/multipage/parsing.html#has-an-element-in-scope

    def __getModeSwitcher(self) -> Union[Callable[[], None], None]:

        def handleInitial(token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
            print("Token type:", token.type)
            if (token.type == HTMLToken.TokenType.DOCTYPE):
                token = cast(HTMLDoctype, token)
                documentNode = DocumentType(token, self.__document)
                self.__document = documentNode
                # TODO: Handle quircks mode.
                self.__switchModeTo(self.__Mode.BeforeHTML)

        def handleBeforeHTML(token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
            if (token.type == HTMLToken.TokenType.StartTag):
                token = cast(HTMLTag, token)
                if (token.name == "html"):
                    element = self.__createElement(token)
                    self.__openElements.push(element)
                    self.__switchModeTo(self.__Mode.BeforeHead)
                else:
                    token = HTMLTag(HTMLToken.TokenType.StartTag)
                    token.name = "html"
                    element = self.__createElement(token)
                    self.__openElements.push(element)
                    self.__switchModeTo(self.__Mode.BeforeHead)

        def handleBeforeHead(token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
            if (token.type == HTMLToken.TokenType.Character):
                if (charIsWhitespace(token.data)):
                    self.__continueIn(self.__Mode.BeforeHead)
            elif (token.type == HTMLToken.TokenType.Comment):
                self.__insertComment(token)
            elif (token.type == HTMLToken.TokenType.DOCTYPE):
                self.__continueIn(self.__Mode.BeforeHead)
            elif (token.type == HTMLToken.TokenType.StartTag):
                token = cast(HTMLTag, token)
                if (token.name == "head"):
                    element = self.__createElement(token)
                    self.__openElements.push(element)
                    self.__switchModeTo(self.__Mode.InHead)
            else:
                token = HTMLTag(HTMLToken.TokenType.StartTag)
                token.name = "head"
                element = self.__createElement(token)
                self.__openElements.push(element)
                self.__switchModeTo(self.__Mode.InHead)

        def handleInHead(token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
            if (token.type == HTMLToken.TokenType.Character):
                if (charIsWhitespace(token.data)):
                    # TODO:Insert the character
                    pass
            elif (token.type == HTMLToken.TokenType.Comment):
                token = cast(HTMLCommentOrCharacter, token)
                comment = Comment(token.data)
                self.__currentElement.appendChild(comment)
            elif (token.type == HTMLToken.TokenType.DOCTYPE):
                pass
            elif (token.type == HTMLToken.TokenType.StartTag):
                token = cast(HTMLTag, token)
                if (token.name == "html"):
                    # TODO: Handle using the "in body"
                    pass
                elif (token.name in ["base", "basefont", "bgsound", "link"]):
                    # This kind of elements are not added to open stack.
                    _ = self.__createElement(token)
                elif (token.name == "meta"):
                    # This kind of elements are not added to open stack.
                    _ = self.__createElement(token)
                    # TODO: Handle charset attribute.
                elif (token.name == "title"):
                    _ = self.__createElement(token)
                    self.__tokenizer.switchStateTo(
                        self.__tokenizer.State.RCDATA)
                    self.__originalInsertionMode = self.__currentInsertionMode
                    self.__currentInsertionMode = self.__Mode.Text
                elif ((token.name == "noscript" and self.__scripting) or (token.name in ["noframes", "style"])):
                    _ = self.__createElement(token)
                    self.__tokenizer.switchStateTo(
                        self.__tokenizer.State.RAWTEXT)
                    self.__originalInsertionMode = self.__currentInsertionMode
                    self.__currentInsertionMode = self.__Mode.Text
                    pass
                elif (token.name == "noscript" and not self.__scripting):
                    _ = self.__createElement(token)
                    self.__switchModeTo(self.__Mode.InHeadNoscript)
                elif (token.name == "script"):
                    # TODO: Add support for JS.
                    pass
                elif (token.name == "template"):
                    # TODO: Handle case.
                    pass
                else:
                    # Ignores "head" and any other tag.
                    pass

            elif (token.type == HTMLToken.TokenType.EndTag):
                if (token.name == "head"):
                    self.__openElements.pop()
                    self.__switchModeTo(self.__Mode.AfterHead)
                elif (token.name in ["body", "html", "br"]):
                    self.__openElements.pop()
                    self.__reconsumeIn(self.__Mode.AfterHead, token)
                elif (token.name == "template"):
                    # TODO: Handle case.
                    pass
            else:
                self.__openElements.pop()
                self.__reconsumeIn(self.__Mode.AfterHead, token)

        def handleInHeadNoscript(token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
            if (token.type == HTMLToken.TokenType.DOCTYPE):
                pass
            elif (token.type == HTMLToken.TokenType.StartTag):
                token = cast(HTMLTag, token)
                if (token.name == "html"):
                    # TODO: Handle using the "in body".
                    pass
            elif (token.type == HTMLToken.TokenType.EndTag):
                token = cast(HTMLTag, token)
                if (token.name == "noscript"):
                    self.__openElements.pop()
                    self.__switchModeTo(self.__Mode.InHead)
                elif (token.name == "br"):
                    self.__openElements.pop()
                else:
                    pass
            elif (token.type == HTMLToken.TokenType.Character):
                if (charIsWhitespace(token.data)):
                    # TODO:Insert the character
                    pass
            elif (token.type == HTMLToken.TokenType.Comment):
                token = cast(HTMLCommentOrCharacter, token)
                comment = Comment(token.data)
                self.__currentElement.appendChild(comment)
            elif (token.type == HTMLToken.TokenType.StartTag):
                if (token.name in ["basefont", "bgsound", "link", "meta", "noframes", "style"]):
                    # TODO: Implement handling.
                    pass
                elif (token.name in ["head", "noscrip"]):
                    pass
            else:
                self.__openElements.pop()

        def handleAfterHead(token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
            if (token.type == HTMLToken.TokenType.Character):
                if (charIsWhitespace(token.data)):
                    self.__insertCharacter(token)
            elif (token.type == HTMLToken.TokenType.Comment):
                self.__insertComment(token)
            elif (token.type == HTMLToken.TokenType.DOCTYPE):
                pass  # Ignore token
            elif (token.type == HTMLToken.TokenType.StartTag):
                token = cast(HTMLTag, token)
                if (token.name == "html"):
                    # TODO: Handle using the "in body".
                    pass
                elif (token.name == "body"):
                    element = self.__createElement(token)
                    self.__openElements.push(element)
                    self.__switchModeTo(self.__Mode.InBody)
                elif (token.name == "frameset"):
                    pass  # TODO: Handle case.
                elif (token.name in ["base", "basefont", "bgsound", "link", "meta", "noframes", "script", "style", "template", "title"]):
                    pass  # TODO: Handle case.
                elif (token.name == "head"):
                    pass  # Ignroe token.
            elif (token.type == HTMLToken.TokenType.EndTag):
                if (token.name == "template"):
                    # TODO: Handle case, Process the token using the rules for the "in head" insertion mode.
                    pass
                elif (token.name in ["body", "html", "br"]):
                    token = HTMLTag(HTMLToken.TokenType.StartTag)
                    token.name = "body"
                    element = self.__createElement(token)
                    self.__openElements.push(element)
                    self.__framesetOK = False
                    self.__reconsumeIn(self.__Mode.InBody, token)
                else:
                    pass  # Ignore token.
            else:
                token = HTMLTag(HTMLToken.TokenType.StartTag)
                token.name = "body"
                element = self.__createElement(token)
                self.__openElements.push(element)
                self.__reconsumeIn(self.__Mode.InBody, token)

        def handleInBody(token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
            if (token.type == HTMLToken.TokenType.Character):
                if (token.data is None):
                    pass  # Ignore token.
                elif (charIsWhitespace(token.data)):
                    # TODO: Reconstruct the active formatting elements, if any.
                    self.__insertCharacter(token)
                else:
                    # TODO: Reconstruct the active formatting elements, if any.
                    self.__insertCharacter(token)
                    self.__framesetOK = False
            elif (token.type == HTMLToken.TokenType.Comment):
                self.__insertComment(token)
            elif (token.type == HTMLToken.TokenType.DOCTYPE):
                pass  # Ignore token.
            elif (token.type == HTMLToken.TokenType.StartTag):
                if (token.name == "html"):
                    pass  # Handle case
                elif (token.name in ["base", "basefont", "bgsound", "link", "meta", "noframes", "script", "style", "template", "title"]):
                    # Handle case, Process the token using the rules for the "in head" insertion mode.
                    pass
                elif (token.name == "body"):
                    pass  # Handle case
                elif (token.name == "frameset"):
                    pass  # Handle case
                elif (token.name in ["address", "article", "aside", "blockquote", "center", "details", "dialog", "dir", "div", "dl", "fieldset", "figcaption", "figure", "footer", "header", "hgroup", "main", "menu", "nav", "ol", "p", "section", "summary", "ul"]):
                    if (self.__openElements.hasInButtonScope("p")):
                        self.__openElements.pop()
                    element = self.__createElement(token)
                    self.__openElements.push(element)
                elif (token.name in ["h1", "h2", "h3", "h4", "h5", "h6"]):
                    if (self.__openElements.hasInButtonScope("p")):
                        self.__openElements.pop()
                    elif (self.__currentElement.name in ["h1", "h2", "h3", "h4", "h5", "h6"]):
                        self.__openElements.pop()
                    element = self.__createElement(token)
                    self.__openElements.push(element)
                elif (token.name in ["pre", "listing"]):
                    pass  # TODO: Handle case
                elif (token.name == "form"):
                    pass  # TODO: Handle case
                elif (token.name == "li"):
                    self.__framesetOK = False
                    element = self.__createElement(token)
                    self.__openElements.push(element)
                    if (self.__currentElement.name == "li"):
                        pass
                    # TODO: Implement rest of the case
                elif (token.name in ["dd", "dt"]):
                    self.__framesetOK = False
                    element = self.__createElement(token)
                    self.__openElements.push(element)
                    # TODO: Handle case
                elif (token.name == "plaintext"):
                    if (self.__openElements.hasInButtonScope("p")):
                        self.__openElements.pop()
                    element = self.__createElement(token)
                    self.__openElements.push(element)
                    self.__tokenizer.switchStateTo(
                        self.__tokenizer.State.PLAINTEXT)
                elif (token.name == "button"):
                    if (self.__elementInOpenStackScope("button")):
                        self.__popElementsFromOpenStackUntilElement()
                    # TODO: Reconstruct the active formatting elements, if any.
                    self.__framesetOK = False
                    element = self.__createElement(token)
                    self.__openElements.push(element)
                elif (token.name == "a"):
                    if (self.__elementInOpenStackScope(token.name)):
                        self.__popElementsFromOpenStackUntilElement(token.name)

                    element = self.__createElement(token)
                    self.__openElements.push(element)
                elif (token.name in ["b", "big", "code", "em", "font", "i", "s", "small", "strike", "strong", "tt", "u"]):
                    # TODO: Reconstruct the active formatting elements, if any and add handling to all tother places too
                    element = self.__createElement(token)
                    self.__openElements.push(element)
                elif (token.name == "nobr"):
                    if (self.__elementInOpenStackScope(token.name)):
                        # TODO: run the adoption agency algorithm for the token
                        pass
                    self.__createElement(token)
                    # TODO: Push onto the list of active formatting elements that element. Add this handling to other places too.

            elif (token.type == HTMLToken.TokenType.EndTag):
                if (token.name == "template"):
                    # Handle case, Process the token using the rules for the "in head" insertion mode.
                    pass
                elif (token.name == "body"):
                    openBodyElement = self.__openElements.lastElementWithTagName(token.name)
                    if (openBodyElement == None):
                        pass  # Ignore token.
                        # TODO: handle the else case.
                    else:
                        self.__switchModeTo(self.__Mode.AfterBody)
                        # TODO: Implement the popping functionality.
                elif (token.name == "html"):
                    self.__reconsumeIn(self.__Mode.AfterBody, token)
                elif (token.name in ["address", "article", "aside", "blockquote", "button", "center", "details", "dialog", "dir", "div", "dl", "fieldset", "figcaption", "figure", "footer", "header", "hgroup", "listing", "main", "menu", "nav", "ol", "pre", "section", "summary", "ul"]):
                    if (not self.__openElements.hasInScope(token.name)):
                        pass
                    elif (not self.__openElements.currentNode().name == token.name):
                        # TODO: Handle parse error
                        pass
                    self.__openElements.popUntilElementWithAtagNameHasBeenPopped(token.name)
                elif (token.name == "form"):
                    # TODO: Handle case
                    pass
                elif (token.name == "p"):
                    if (self.__openElements.hasInButtonScope("p")):
                        self.__openElements.pop()
                    element = self.__createElement(token)
                    self.__openElements.push(element)
                elif (token.name == "li"):
                    # TODO: Handle case
                    pass
                elif (token.name in ["dd", "dt"]):
                    # TODO: Handle case
                    pass
                elif (token.name in ["h1", "h2", "h3", "h4", "h5", "h6"]):
                    if (self.__currentElement.name == token.name):
                        self.__openElements.pop()
                elif (token.name == "sarcasm"):
                    # TODO: Handle case
                    pass
                elif (token.name in ["a", "b", "big", "code", "em", "font", "i", "nobr", "s", "small", "strike", "strong", "tt", "u"]):
                    # TODO: Run the adoption agency algorithm for the token.
                    pass

            elif (token.type == HTMLToken.TokenType.EOF):
                pass  # TODO: Handle case.

        def handleText(token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
            if (token.type == HTMLToken.TokenType.Character):
                self.__insertCharacter(token)
            elif (token.type == HTMLToken.TokenType.EOF):
                # TODO: Handle case
                pass
            elif (token.type == HTMLToken.TokenType.EndTag):
                if(token.name == "script"):
                    # TODO: handle case
                    pass
            else:
                self.__openElements.pop()
                self.__switchModeTo(self.__originalInsertionMode)

        def handleInTable() -> None:
            return

        def handleInTableText() -> None:
            return

        def handleInCaption() -> None:
            return

        def handleInColumnGroup() -> None:
            return

        def handleInTableBody() -> None:
            return

        def handleInRow() -> None:
            return

        def handleInCell() -> None:
            return

        def handleInSelect() -> None:
            return

        def handleInSelectInTable() -> None:
            return

        def handleInTemplate() -> None:
            return

        def handleAfterBody(token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
            return

        def handleInFrameset() -> None:
            return

        def handleAfterFrameset() -> None:
            return

        def handleAfterAfterBody() -> None:
            return

        def handleAfterAfterFrameset() -> None:
            return

        switcher = {
            self.__Mode.Initial: handleInitial,
            self.__Mode.BeforeHTML: handleBeforeHTML,
            self.__Mode.BeforeHead: handleBeforeHead,
            self.__Mode.InHead: handleInHead,
            self.__Mode.InHeadNoscript: handleInHeadNoscript,
            self.__Mode.AfterHead: handleAfterHead,
            self.__Mode.InBody: handleInBody,
            self.__Mode.Text: handleText,
            self.__Mode.InTable: handleInTable,
            self.__Mode.InTableText: handleInTableText,
            self.__Mode.InCaption: handleInCaption,
            self.__Mode.InColumnGroup: handleInColumnGroup,
            self.__Mode.InTableBody: handleInTableBody,
            self.__Mode.InRow: handleInRow,
            self.__Mode.InCell: handleInCell,
            self.__Mode.InSelect: handleInSelect,
            self.__Mode.InSelectInTable: handleInSelectInTable,
            self.__Mode.InTemplate: handleInTemplate,
            self.__Mode.AfterBody: handleAfterBody,
            self.__Mode.InFrameset: handleInFrameset,
            self.__Mode.AfterFrameset: handleAfterFrameset,
            self.__Mode.AfterAfterBody: handleAfterAfterBody,
            self.__Mode.AfterAfterFrameset: handleAfterAfterFrameset,
        }

        return switcher.get(self.__currentInsertionMode, None)

    def currentInsertionMode(self) -> __Mode:
        return self.__currentInsertionMode

    def nextToken(self) -> Union[HTMLToken, None]:
        return
