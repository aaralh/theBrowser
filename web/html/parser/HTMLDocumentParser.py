from enum import Enum, Flag, auto
from os import name
from typing import Any, List, Union, Callable, cast
from web.dom.elements.HTMLScriptElement import HTMLScriptElement
from web.dom.elements.HTMLTemplateElement import HTMLTemplateElement
from web.html.parser.ListOfActiveElements import ListOfActiveElements
from web.html.parser.StackOfOpenElments import StackOfOpenElments
from web.dom.CharacterData import CharacterData
from web.dom.elements.Comment import Comment
from web.html.parser.utils import charIsWhitespace, tagIsSpecial
from web.dom.elements.Element import Element
from web.dom.Document import Document
from web.dom.Node import Node
from web.dom.elements.Text import Text
from web.dom.DocumentType import DocumentType
from web.html.parser.HTMLToken import HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter
from web.html.parser.HTMLTokenizer import HTMLTokenizer
from web.dom.ElementFactory import ElementFactory
from dataclasses import dataclass
from copy import deepcopy


class HTMLDocumentParser:
    @dataclass
    class AdjustedInsertionLocation:
        parent: Union[Element, None] = None
        insertBeforeSibling: Union[Element, None] = None  # If none insert as last child.

    class _Mode(Enum):
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
        self._currentInsertionMode = self._Mode.Initial
        self._originalInsertionMode: Union[self._Mode, None] = None
        self._openElements = StackOfOpenElments()
        self._tokenizer = HTMLTokenizer(html, self._tokenHandler)
        self._document = Document()
        self._documentNode = None
        self._scripting: bool = False
        self._framesetOK: bool = True
        self._formattingElements = ListOfActiveElements()
        self._fosterParenting: bool = False
        self.parsingFragment: bool = False
        self.invokefWhileDocumentWrite: bool = False
        self._formElement: Union[Element, None] = None
        self.__cb: Union[Callable, None] = None

    @property
    def _currentElement(self) -> Node:
        """
        Gets the latest opened element aka "parent".
        """
        return self._documentNode if self._openElements.isEmpty() else self._openElements.last()

    def run(self, cb: Callable) -> None:
        self.__cb = cb
        self._tokenizer.run()

    def _tokenHandler(self, token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:

        print("Token: ", token)
        print("Input mode: ", self._currentInsertionMode)
        print("self._openElements")
        print("Elements: ", self._openElements.elements())

        switcher = self._getModeSwitcher()
        if switcher is not None:
            switcher(token)

        if token.type == HTMLToken.TokenType.EOF:
            print("The dom")
            print(self._documentNode)
            self.__cb(self._documentNode)

    def _continueIn(self, mode: _Mode) -> None:
        self._switchModeTo(mode)

    def _switchModeTo(self, newMode: _Mode) -> None:
        """
        Switch state and consume next character.
        """
        self._currentInsertionMode = newMode

    def _reconsumeIn(self, newMode: _Mode,
                     token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
        """
        Switch state without consuming next character.
        """
        self._currentInsertionMode = newMode
        switcher = self._getModeSwitcher()
        if switcher is not None:
            switcher(token)

    def _createElement(self, token: HTMLTag) -> Element:
        """
        Creates element based on given token and sets parent for it.
        """
        parent = self._currentElement
        element = ElementFactory.create_element(token, parent, self._document)
        element.parentNode.appendChild(element)

        return element

    def _createElementWihtAdjustedLocation(self, token: HTMLTag, adjustedLocation: AdjustedInsertionLocation):
        """
        Creates element based on given token and inserts it based on adjsuted location.
        """
        parent = adjustedLocation.parent
        element = ElementFactory.create_element(token, parent, self._document)
        if adjustedLocation.insertBeforeSibling is None:
            element.parentNode.appendChild(element)
        else:
            element.parentNode.appendChildBeforeElement(adjustedLocation.insertBeforeSibling)

        return element

    def _insertCharacter(self, token: HTMLCommentOrCharacter) -> None:
        if type(self._currentElement) is Document:
            return
        elif len(self._currentElement.childNodes) > 0 and type(self._currentElement.childNodes[-1]) is Text:
            cast(Text, self._currentElement.childNodes[-1]).appendData(token.data)
        else:
            textNode = Text(self._document, self._currentElement, token.data)
            textNode.parentNode = self._currentElement
            self._currentElement.appendChild(textNode)

    def _insertComment(self, token: HTMLCommentOrCharacter) -> None:
        comment = Comment(token.data)
        comment.parentNode = self._currentElement
        self._currentElement.appendChild(comment)
        self._continueIn(self._Mode.BeforeHead)

    def _adoptionAgencyAlgorithm(self, token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
        subject = token.name
        if self._currentElement.name == subject and not self._formattingElements.contains(self._currentElement):
            self._openElements.pop()
            return
        outerLoopCounter = 0

        while outerLoopCounter < 8:
            outerLoopCounter += 1
            formattingElementResult = self._formattingElements.lastElementWithTagNameBeforeMarker(subject)
            if formattingElementResult is None:
                return
            formattingElement = formattingElementResult.element

            if not self._openElements.containsElement(formattingElement):
                self._formattingElements.remove(formattingElement)
                return
            if self._openElements.containsElement(formattingElement) and not self._openElements.hasInScope():
                return
            if formattingElement != self._currentElement:
                # TODO: Handle parsing error.
                pass

            furtherMostBlock = self._openElements.topmostSpecialNodeBelow(formattingElement)

            if furtherMostBlock is None:
                self._openElements.popUntilElementWithAtagNameHasBeenPopped(formattingElement.name)
                self._formattingElements.remove(formattingElement)
                return

            """ commonAncestor = self._openElements.elementBefore(formattingElement)
            bookMark = formattingElementResult.index

            node = deepcopy(furtherMostBlock.element)
            lastNode = deepcopy(furtherMostBlock.element)
            innerLoopCounter = 0
            while (innerLoopCounter <= 3):
                node = self._openElements.elementBefore(node)
                if (node is None):
                    node = self._openElements.getElementOnIndex(fur) """

        # bookmark =
        # case 13
        # TODO: Continue here https://html.spec.whatwg.org/multipage/parsing.html#adoption-agency-algorithm
        # https://html.spec.whatwg.org/multipage/parsing.html#has-an-element-in-scope

    def _generateImpliedEndTags(self, exception: str = None) -> None:
        while (self._currentElement.name != exception and self._currentElement.name in ["caption", "colgroup", "dd",
                                                                                        "dt", "li", "optgroup",
                                                                                        "option", "p", "rb", "rp", "rt",
                                                                                        "rtc", "tbody", "td", "tfoot",
                                                                                        "th", "thead", "tr"]):
            self._openElements.pop()

    def _closeAPElement(self) -> None:
        self._generateImpliedEndTags("p")
        if self._currentElement.name != "p":
            # TODO: Handle parse error.
            pass
        self._openElements.popUntilElementWithAtagNameHasBeenPopped("p")

    def _findAppropriatePlaceForInsertingNode(self) -> AdjustedInsertionLocation:
        target = self._currentElement
        adjustedLocation = self.AdjustedInsertionLocation()

        if self._fosterParenting and target.name in ["table", "tbody", "tfoot", "thead", "tr"]:
            templateResult = self._openElements.lastElementWithTagName("template")
            tableResult = self._openElements.lastElementWithTagName("table")
            if (templateResult is not None and tableResult is None or (
                    tableResult is not None and tableResult.index < templateResult.index)):
                adjustedLocation.parent = templateResult.element
                adjustedLocation.insertBeforeSibling = None
                return adjustedLocation
            elif tableResult is None:
                adjustedLocation.parent = self._openElements.first()
                adjustedLocation.insertBeforeSibling = None
                return adjustedLocation
            elif tableResult is not None and tableResult.element.parentNode is not None:
                adjustedLocation.parent = tableResult.element.parentNode
                adjustedLocation.insertBeforeSibling = tableResult.element
                return adjustedLocation

            previousElement = self._openElements.elementBefore(tableResult.element)
            adjustedLocation.parent = previousElement
            adjustedLocation.insertBeforeSibling = None
            return adjustedLocation
        else:
            adjustedLocation.parent = target
            adjustedLocation.insertBeforeSibling = None

        if adjustedLocation.parent.name == "template":
            adjustedLocation.parent = cast(HTMLTemplateElement, adjustedLocation.parent).content
            adjustedLocation.insertBeforeSibling = None

        return adjustedLocation

    def _getModeSwitcher(self) -> Union[Callable[[], None], None]:

        def handleInitial(token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
            if token.type == HTMLToken.TokenType.DOCTYPE:
                token = cast(HTMLDoctype, token)
                documentNode = DocumentType(token, self._document)
                self._documentNode = documentNode
                # TODO: Handle quircks mode.
                self._switchModeTo(self._Mode.BeforeHTML)

        def handleBeforeHTML(token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
            if token.type == HTMLToken.TokenType.StartTag:
                token = cast(HTMLTag, token)
                if token.name == "html":
                    element = self._createElement(token)
                    self._openElements.push(element)
                    self._switchModeTo(self._Mode.BeforeHead)
                else:
                    token = HTMLTag(HTMLToken.TokenType.StartTag)
                    token.name = "html"
                    element = self._createElement(token)
                    self._openElements.push(element)
                    self._switchModeTo(self._Mode.BeforeHead)

        def handleBeforeHead(token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
            if token.type == HTMLToken.TokenType.Character:
                if charIsWhitespace(token.data):
                    self._continueIn(self._Mode.BeforeHead)
            elif token.type == HTMLToken.TokenType.Comment:
                self._insertComment(token)
            elif token.type == HTMLToken.TokenType.DOCTYPE:
                self._continueIn(self._Mode.BeforeHead)
            elif token.type == HTMLToken.TokenType.StartTag:
                token = cast(HTMLTag, token)
                if token.name == "head":
                    element = self._createElement(token)
                    self._openElements.push(element)
                    self._switchModeTo(self._Mode.InHead)
            else:
                token = HTMLTag(HTMLToken.TokenType.StartTag)
                token.name = "head"
                element = self._createElement(token)
                self._openElements.push(element)
                self._switchModeTo(self._Mode.InHead)

        def handleInHead(token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
            if token.type == HTMLToken.TokenType.Character:
                if charIsWhitespace(token.data):
                    self._insertCharacter(token)
            elif token.type == HTMLToken.TokenType.Comment:
                token = cast(HTMLCommentOrCharacter, token)
                comment = Comment(token.data)
                self._currentElement.appendChild(comment)
            elif token.type == HTMLToken.TokenType.DOCTYPE:
                pass
            elif token.type == HTMLToken.TokenType.StartTag:
                token = cast(HTMLTag, token)
                if token.name == "html":
                    # TODO: Handle using the "in body"
                    raise NotImplementedError
                elif token.name in ["base", "basefont", "bgsound", "link"]:
                    # This kind of elements are not added to open stack.
                    _ = self._createElement(token)
                elif token.name == "meta":
                    # This kind of elements are not added to open stack.
                    element = self._createElement(token)
                    if "charset" in element.attributes:
                        # TODO: Handle charset attribute.
                        pass

                elif token.name == "title":
                    element = self._createElement(token)
                    self._openElements.push(element)
                    self._tokenizer.switchStateTo(
                        self._tokenizer.State.RCDATA)
                    print("Assigning insertion mode:", self._currentInsertionMode)
                    self._originalInsertionMode = self._currentInsertionMode
                    self._switchModeTo(self._Mode.Text)
                elif (token.name == "noscript" and self._scripting) or (token.name in ["noframes", "style"]):
                    element = self._createElement(token)
                    self._openElements.push(element)
                    self._tokenizer.switchStateTo(
                        self._tokenizer.State.RAWTEXT)
                    self._originalInsertionMode = self._currentInsertionMode
                    self._switchModeTo(self._Mode.Text)
                elif token.name == "noscript" and not self._scripting:
                    _ = self._createElement(token)
                    self._switchModeTo(self._Mode.InHeadNoscript)
                elif token.name == "script":
                    # TODO: Add support for JS.
                    adjustedInsertionLocation = self._findAppropriatePlaceForInsertingNode()
                    element = cast(HTMLScriptElement,
                                   self._createElementWihtAdjustedLocation(token, adjustedInsertionLocation))
                    element.parserDocument = self._document
                    element.isNonBlocking = False

                    if self.parsingFragment:
                        raise NotImplementedError
                    if self.invokefWhileDocumentWrite:
                        raise NotImplementedError

                    self._openElements.push(element)
                    self._tokenizer.switchStateTo(self._tokenizer.State.ScriptData)
                    self._originalInsertionMode = self._currentInsertionMode
                    self._switchModeTo(self._Mode.Text)

                elif token.name == "template":
                    # TODO: Handle case.
                    raise NotImplementedError
                else:
                    # Ignores "head" and any other tag.
                    pass

            elif token.type == HTMLToken.TokenType.EndTag:
                if token.name == "head":
                    self._openElements.pop()
                    self._switchModeTo(self._Mode.AfterHead)
                elif token.name in ["body", "html", "br"]:
                    self._openElements.pop()
                    self._reconsumeIn(self._Mode.AfterHead, token)
                elif token.name == "template":
                    # TODO: Handle case.
                    raise NotImplementedError
            else:
                self._openElements.pop()
                self._reconsumeIn(self._Mode.AfterHead, token)

        def handleInHeadNoscript(token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
            if token.type == HTMLToken.TokenType.DOCTYPE:
                pass
            elif token.type == HTMLToken.TokenType.StartTag:
                token = cast(HTMLTag, token)
                if token.name == "html":
                    # TODO: Handle using the "in body".
                    raise NotImplementedError
            elif token.type == HTMLToken.TokenType.EndTag:
                token = cast(HTMLTag, token)
                if token.name == "noscript":
                    self._openElements.pop()
                    self._switchModeTo(self._Mode.InHead)
                elif token.name == "br":
                    self._openElements.pop()
                else:
                    pass
            elif token.type == HTMLToken.TokenType.Character:
                if charIsWhitespace(token.data):
                    # TODO:Insert the character
                    raise NotImplementedError
            elif token.type == HTMLToken.TokenType.Comment:
                token = cast(HTMLCommentOrCharacter, token)
                comment = Comment(token.data)
                self._currentElement.appendChild(comment)
            elif token.type == HTMLToken.TokenType.StartTag:
                if token.name in ["basefont", "bgsound", "link", "meta", "noframes", "style"]:
                    # TODO: Implement handling.
                    raise NotImplementedError
                elif token.name in ["head", "noscrip"]:
                    pass
            else:
                self._openElements.pop()

        def handleAfterHead(token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
            if token.type == HTMLToken.TokenType.Character:
                if charIsWhitespace(token.data):
                    self._insertCharacter(token)
            elif token.type == HTMLToken.TokenType.Comment:
                self._insertComment(token)
            elif token.type == HTMLToken.TokenType.DOCTYPE:
                pass  # Ignore token
            elif token.type == HTMLToken.TokenType.StartTag:
                token = cast(HTMLTag, token)
                if token.name == "html":
                    # TODO: Handle using the "in body".
                    raise NotImplementedError
                elif token.name == "body":
                    element = self._createElement(token)
                    self._openElements.push(element)
                    self._switchModeTo(self._Mode.InBody)
                elif token.name == "frameset":
                    raise NotImplementedError  # TODO: Handle case.
                elif (token.name in ["base", "basefont", "bgsound", "link", "meta", "noframes", "script", "style",
                                     "template", "title"]):
                    raise NotImplementedError  # TODO: Handle case.
                elif token.name == "head":
                    pass  # Ignroe token.
            elif token.type == HTMLToken.TokenType.EndTag:
                if token.name == "template":
                    # TODO: Handle case, Process the token using the rules for the "in head" insertion mode.
                    raise NotImplementedError
                elif token.name in ["body", "html", "br"]:
                    _token = HTMLTag(HTMLToken.TokenType.StartTag)
                    _token.name = "body"
                    element = self._createElement(_token)
                    self._openElements.push(element)
                    self._framesetOK = False
                    self._reconsumeIn(self._Mode.InBody, token)
                else:
                    pass  # Ignore token.
            else:
                _token = HTMLTag(HTMLToken.TokenType.StartTag)
                _token.name = "body"
                element = self._createElement(_token)
                self._openElements.push(element)
                self._reconsumeIn(self._Mode.InBody, token)

        def handleInBody(token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
            if token.type == HTMLToken.TokenType.Character:
                if token.data is None:
                    pass  # Ignore token.
                elif charIsWhitespace(token.data):
                    # TODO: Reconstruct the active formatting elements, if any.
                    self._insertCharacter(token)
                else:
                    # TODO: Reconstruct the active formatting elements, if any.
                    self._insertCharacter(token)
                    self._framesetOK = False
            elif token.type == HTMLToken.TokenType.Comment:
                self._insertComment(token)
            elif token.type == HTMLToken.TokenType.DOCTYPE:
                pass  # Ignore token.
            elif token.type == HTMLToken.TokenType.StartTag:
                if token.name == "html":
                    raise NotImplementedError  # Handle case
                elif token.name == "template":
                    # Handle case, Process the token using the rules for the "in head" insertion mode.
                    raise NotImplementedError
                elif token.name in ["noframes", "style"]:
                    element = self._createElement(token)
                    self._openElements.push(element)
                    self._tokenizer.switchStateTo(
                        self._tokenizer.State.RAWTEXT)
                    self._originalInsertionMode = self._currentInsertionMode
                    self._switchModeTo(self._Mode.Text)
                elif token.name in ["base", "basefont", "bgsound", "link"]:
                    # This kind of elements are not added to open stack.
                    _ = self._createElement(token)
                elif token.name == "meta":
                    # This kind of elements are not added to open stack.
                    element = self._createElement(token)
                    if "charset" in element.attributes:
                        # TODO: Handle charset attribute.
                        pass
                elif token.name == "title":
                    element = self._createElement(token)
                    self._openElements.push(element)
                    self._tokenizer.switchStateTo(
                        self._tokenizer.State.RCDATA)
                    self._originalInsertionMode = self._currentInsertionMode
                    self._switchModeTo(self._Mode.Text)
                elif token.name == "script":
                    # TODO: Add support for JS.
                    adjustedInsertionLocation = self._findAppropriatePlaceForInsertingNode()
                    element = cast(HTMLScriptElement,
                                   self._createElementWihtAdjustedLocation(token, adjustedInsertionLocation))
                    element.parserDocument = self._document
                    element.isNonBlocking = False

                    if self.parsingFragment:
                        raise NotImplementedError
                    if self.invokefWhileDocumentWrite:
                        raise NotImplementedError

                    self._openElements.push(element)
                    self._tokenizer.switchStateTo(self._tokenizer.State.ScriptData)
                    self._originalInsertionMode = self._currentInsertionMode
                    self._switchModeTo(self._Mode.Text)
                elif token.name == "body":
                    # TODO: handle parse error.
                    pass
                elif token.name == "frameset":
                    raise NotImplementedError  # Handle case
                elif (token.name in ["address", "article", "aside", "blockquote", "center", "details", "dialog", "dir",
                                     "div", "dl", "fieldset", "figcaption", "figure", "footer", "header", "hgroup",
                                     "main", "menu", "nav", "ol", "p", "section", "summary", "ul"]):
                    if self._openElements.hasInButtonScope("p"):
                        self._openElements.pop()
                    element = self._createElement(token)
                    self._openElements.push(element)
                elif token.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                    if self._openElements.hasInButtonScope("p"):
                        self._openElements.pop()
                    elif self._currentElement.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                        self._openElements.pop()
                    element = self._createElement(token)
                    self._openElements.push(element)
                elif token.name in ["pre", "listing"]:
                    raise NotImplementedError  # TODO: Handle case
                elif token.name == "form":
                    if self._formElement is not None and self._openElements.contains("template") is False:
                        # TODO: Handle parse error.
                        pass
                    elif self._openElements.hasInButtonScope("p"):
                        self._openElements.popUntilElementWithAtagNameHasBeenPopped("p")

                    element = self._createElement(token)
                    self._openElements.push(element)

                    if self._openElements.contains("template") is False:
                        self._formElement = element
                elif token.name == "li":
                    self._framesetOK = False

                    for element in reversed(self._openElements.elements()):
                        node = element
                        if self._currentElement.name == "li":
                            self._generateImpliedEndTags("li")
                            if self._currentElement.name == "li":
                                # TODO: Handle parse error
                                pass
                            self._openElements.popUntilElementWithAtagNameHasBeenPopped("li")
                            break

                        if tagIsSpecial(node.name) and node.name not in ["address", "div", "p"]:
                            break

                    if self._openElements.hasInButtonScope("p"):
                        self._closeAPElement()

                    element = self._createElement(token)
                    self._openElements.push(element)

                elif token.name in ["dd", "dt"]:
                    self._framesetOK = False
                    element = self._createElement(token)
                    self._openElements.push(element)
                    # TODO: Handle case
                    raise NotImplementedError
                elif token.name == "plaintext":
                    if self._openElements.hasInButtonScope("p"):
                        self._openElements.pop()
                    element = self._createElement(token)
                    self._openElements.push(element)
                    self._tokenizer.switchStateTo(
                        self._tokenizer.State.PLAINTEXT)
                elif token.name == "button":
                    if self._openElements.hasInScope(token.name):
                        self._openElements.popUntilElementWithAtagNameHasBeenPopped(token.name)
                    # TODO: Reconstruct the active formatting elements, if any.
                    self._framesetOK = False
                    element = self._createElement(token)
                    self._openElements.push(element)
                elif token.name == "a":
                    if self._openElements.hasInScope(token.name):
                        self._openElements.popUntilElementWithAtagNameHasBeenPopped(token.name)

                    element = self._createElement(token)
                    self._openElements.push(element)
                elif (token.name in ["b", "big", "code", "em", "font", "i", "s", "small", "strike", "strong", "tt",
                                     "u"]):
                    # TODO: Reconstruct the active formatting elements, if any and add handling to all tother places too
                    element = self._createElement(token)
                    self._openElements.push(element)
                elif token.name == "nobr":
                    if self._openElements.hasInScope(token.name):
                        # TODO: run the adoption agency algorithm for the token
                        raise NotImplementedError
                    self._createElement(token)
                # TODO: Push onto the list of active formatting elements that element. Add this handling to other places too.
                elif token.name in ["area", "br", "embed", "img", "keygen", "wbr"]:
                    # TODO: Construct active elements.
                    element = self._createElement(token)
                    self._openElements.push(element)
                    self._openElements.pop()
                elif token.name == "textarea":
                    element = self._createElement(token)
                    self._openElements.push(element)
                    # TODO: Handle new line
                    self._tokenizer.switchStateTo(self._tokenizer.State.RCDATA)
                    self._originalInsertionMode = self._currentInsertionMode
                    self._framesetOK = False
                    self._switchModeTo(self._Mode.Text)
                else:
                    # TODO: Construct active elements.
                    element = self._createElement(token)
                    self._openElements.push(element)
            elif token.type == HTMLToken.TokenType.EndTag:
                if token.name == "template":
                    # Handle case, Process the token using the rules for the "in head" insertion mode.
                    raise NotImplementedError
                elif token.name == "body":
                    print("Closing body element")
                    openBodyElement = self._openElements.lastElementWithTagName(token.name)
                    if openBodyElement is None:
                        print("No body tag in open stack")
                        pass  # Ignore token.
                    # TODO: handle the else case.
                    else:
                        self._switchModeTo(self._Mode.AfterBody)
                        self._openElements.popUntilElementWithAtagNameHasBeenPopped(token.name)
                        # TODO: Implement the popping functionality.
                        self._switchModeTo(self._Mode.AfterBody)
                elif token.name == "html":
                    self._reconsumeIn(self._Mode.AfterBody, token)
                elif (token.name in ["address", "article", "aside", "blockquote", "button", "center", "details",
                                     "dialog", "dir", "div", "dl", "fieldset", "figcaption", "figure", "footer",
                                     "header", "hgroup", "listing", "main", "menu", "nav", "ol", "pre", "section",
                                     "summary", "ul"]):
                    if not self._openElements.hasInScope(token.name):
                        pass
                    else:
                        # TODO: Generate implied end tags
                        if not self._openElements.currentNode().name == token.name:
                            # TODO: Handle parse error
                            pass

                        self._openElements.popUntilElementWithAtagNameHasBeenPopped(token.name)
                elif token.name == "form":
                    if self._openElements.contains("template") is False:
                        node = self._formElement
                        self._formElement = None
                        if node is None or self._openElements.hasInScope(node.name) is False:
                            # TODO: Handle parse error.
                            return
                        self._generateImpliedEndTags()
                        if self._currentElement != node:
                            # TODO: Handle parse error
                            pass
                        self._openElements.popUntilElementWithAtagNameHasBeenPopped(node.name)
                    else:
                        if self._openElements.hasInScope("form"):
                            # TODO: Handle parse error.
                            return
                        self._generateImpliedEndTags()
                        if self._currentElementname != "form":
                            # TODO: Handle parse error
                            pass
                        self._openElements.popUntilElementWithAtagNameHasBeenPopped("form")

                elif token.name == "p":
                    if not self._openElements.hasInButtonScope("p"):
                        element = self._createElement(token)
                        self._openElements.push(element)
                    self._openElements.pop()
                elif token.name == "li":
                    if not self._openElements.hasInListItemScope(token.name):
                        # TODO: Handle parse rror.
                        return

                    self._generateImpliedEndTags(token.name)
                    if self._currentElement.name != "li":
                        # TODO: Handle parse error.
                        pass
                    print("Removing 'li'")
                    self._openElements.popUntilElementWithAtagNameHasBeenPopped("li")
                elif token.name in ["dd", "dt"]:
                    # TODO: Handle case
                    raise NotImplementedError
                elif token.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                    if not self._openElements.hasInScope(token.name):
                        raise NotImplementedError  # TODO: handle parse error.
                        return

                    if self._currentElement.name != token.name:
                        raise NotImplementedError  # TODO: handle parse error.

                    while not self._openElements.isEmpty():
                        poppedElement = self._openElements.pop()
                        if poppedElement.name == token.name:
                            break
                    return
                elif token.name == "sarcasm":
                    # TODO: Handle case
                    raise NotImplementedError
                elif (token.name in ["a", "b", "big", "code", "em", "font", "i", "nobr", "s", "small", "strike",
                                     "strong", "tt", "u"]):
                    # TODO: Run the adoption agency algorithm for the token.
                    self._adoptionAgencyAlgorithm(token)
                else:
                    node: Union[Element, None] = None

                    for element in reversed(self._openElements.elements()):
                        node = element
                        if node.name == token.name:
                            self._generateImpliedEndTags(token.name)
                            if node != self._currentElement:
                                # TODO: Handle parse error.
                                pass

                            while self._currentElement.name != node.name:
                                self._openElements.pop()

                            self._openElements.pop()
                            break

                        if tagIsSpecial(node.name):
                            # TODO: Handle parse error.
                            return


            elif token.type == HTMLToken.TokenType.EOF:
                for node in self._openElements.elements():
                    if node.name not in ["dd", "dt", "li", "optgroup", "option", "p", "rb", "rp", "rt", "rtc", "tbody",
                                         "td", "tfoot", "th", "thead", "tr", "body", "html"]:
                        # TODO: Handle parse error.
                        break
                return

        def handleText(token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
            if token.type == HTMLToken.TokenType.Character:
                self._insertCharacter(token)
            elif token.type == HTMLToken.TokenType.EOF:
                if self._currentElement.name == "script":
                    # TODO: Mark the script element as "already started".
                    pass
                self._openElements.pop()
                self._reconsumeIn(self._originalInsertionMode, token)
            elif token.type == HTMLToken.TokenType.EndTag and token.name == "script":
                # TODO: flush_character_insertions()
                script = self._currentElement
                self._openElements.pop()
                self._switchModeTo(self._originalInsertionMode)
            # TODO: HAndle rest of the case.
            else:
                self._openElements.pop()
                self._switchModeTo(self._originalInsertionMode)

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
            if token.type == HTMLToken.TokenType.EOF:
                self._openElements.popAllElements()
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
            self._Mode.Initial: handleInitial,
            self._Mode.BeforeHTML: handleBeforeHTML,
            self._Mode.BeforeHead: handleBeforeHead,
            self._Mode.InHead: handleInHead,
            self._Mode.InHeadNoscript: handleInHeadNoscript,
            self._Mode.AfterHead: handleAfterHead,
            self._Mode.InBody: handleInBody,
            self._Mode.Text: handleText,
            self._Mode.InTable: handleInTable,
            self._Mode.InTableText: handleInTableText,
            self._Mode.InCaption: handleInCaption,
            self._Mode.InColumnGroup: handleInColumnGroup,
            self._Mode.InTableBody: handleInTableBody,
            self._Mode.InRow: handleInRow,
            self._Mode.InCell: handleInCell,
            self._Mode.InSelect: handleInSelect,
            self._Mode.InSelectInTable: handleInSelectInTable,
            self._Mode.InTemplate: handleInTemplate,
            self._Mode.AfterBody: handleAfterBody,
            self._Mode.InFrameset: handleInFrameset,
            self._Mode.AfterFrameset: handleAfterFrameset,
            self._Mode.AfterAfterBody: handleAfterAfterBody,
            self._Mode.AfterAfterFrameset: handleAfterAfterFrameset,
        }

        return switcher.get(self._currentInsertionMode, None)

    def currentInsertionMode(self) -> _Mode:
        return self._currentInsertionMode

    def nextToken(self) -> Union[HTMLToken, None]:
        return
