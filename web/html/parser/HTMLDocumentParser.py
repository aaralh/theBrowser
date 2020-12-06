from enum import Enum, auto
from typing import Any, List, Union, Callable, cast
from web.dom.CharacterData import CharacterData
from web.dom.Comment import Comment
from web.html.parser.utils import charIsWhitespace
from web.dom.Element import Element
from web.dom.Document import Document
from web.dom.Node import Node
from web.dom.Text import Text
from web.dom.DocumentType import DocumentType
from web.html.parser.HTMLToken import HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter
from web.html.parser.HTMLTokenizer import HTMLTokenizer



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
        self.__openElements: List[Node] = []
        self.__tokenizer = HTMLTokenizer(html, self.__tokenHandler)
        self.__document = Document()
        self.__currentElement = self.__document
        self.__scripting: bool = False
        self.__framesetOK: bool = True

    def run(self) -> None:
        self.__tokenizer.run()

    def __getOpenElement(self) -> Node:
        '''
        Gets the latest opened element aka "parent".
        '''
        return self.__document if (len(self.__openElements) == 0) else self.__openElements[-1]

    def __tokenHandler(self, token: Any) -> None:
        print(token)
        print(self.__document)
        print(self.__openElements)
        print(self.__currentInsertionMode)
        
        switcher = self.__getModeSwitcher()
        if (switcher != None):
            switcher(token)
        print(self.__currentInsertionMode)
        print()


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
        element = Element(token, parent, parent.document)
        element.parentNode.appendChild(element)

        return element

    def __addToOpenStack(self, node: Node) -> None:
        self.__openElements.append(node)
        self.__currentElement = node


    def __removeCurrentFromOpenStack(self) -> None:
        self.__openElements.remove(self.__currentElement)
        self.__currentElement = self.__getOpenElement()

    def __insertCharacter(self, token: HTMLCommentOrCharacter) -> None:
        if (type(self.__currentElement) is Document):
            return
        elif (type(self.__currentElement.childNodes[-1]) is Text):
            cast(Text, self.__currentElement.childNodes[-1]).appendData(token.data)
        else:
            textNode = Text(token.data)
            textNode.parentNode = self.__currentElement
            self.__currentElement.appendChild(textNode)

    def __insertComment(self, token: HTMLCommentOrCharacter) -> None:
        comment = Comment(token.data)
        comment.parentNode = self.__currentElement
        self.__currentElement.appendChild(comment)
        self.__continueIn(self.__Mode.BeforeHead)

    def __getModeSwitcher(self) -> Union[Callable[[], None], None]:

        def handleInitial(token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
            print("Token type:", token.type)
            if (token.type == HTMLToken.TokenType.DOCTYPE):
                token = cast(HTMLDoctype, token)
                documentNode = DocumentType(token, self.__document)
                self.__document = documentNode
                #TODO: Handle quircks mode.
                self.__switchModeTo(self.__Mode.BeforeHTML)
                
                
        def handleBeforeHTML(token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
            if (token.type == HTMLToken.TokenType.StartTag):
                token = cast(HTMLTag, token)
                if (token.name == "html"):
                    element = self.__createElement(token)
                    self.__addToOpenStack(element)
                    self.__switchModeTo(self.__Mode.BeforeHead)
                else:
                    token = HTMLTag(HTMLToken.TokenType.StartTag)
                    token.name = "html"
                    element = self.__createElement(token)
                    self.__addToOpenStack(element)
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
                    self.__addToOpenStack(element)
                    self.__switchModeTo(self.__Mode.InHead)
            else:
                token = HTMLTag(HTMLToken.TokenType.StartTag)
                token.name = "head"
                element = self.__createElement(token)
                self.__addToOpenStack(element)
                self.__switchModeTo(self.__Mode.InHead)

        def handleInHead(token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
            if (token.type == HTMLToken.TokenType.Character):
                if (charIsWhitespace(token.data)):
                    #TODO:Insert the character
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
                    #TODO: Handle using the "in body"
                    pass
                elif (token.name in ["base", "basefont", "bgsound", "link"]):
                    # This kind of elements are not added to open stack.
                    _ = self.__createElement(token)
                elif (token.name == "meta"):
                    # This kind of elements are not added to open stack.
                    _ = self.__createElement(token)
                    #TODO: Handle charset attribute.
                elif (token.name == "title"):   
                    _ = self.__createElement(token)
                    self.__tokenizer.switchStateTo(self.__tokenizer.State.RCDATA)
                    self.__originalInsertionMode = self.__currentInsertionMode
                    self.__currentInsertionMode = self.__Mode.Text
                elif ((token.name == "noscript" and self.__scripting) or (token.name in ["noframes", "style"])):
                    _ = self.__createElement(token)
                    self.__tokenizer.switchStateTo(self.__tokenizer.State.RAWTEXT)
                    self.__originalInsertionMode = self.__currentInsertionMode
                    self.__currentInsertionMode = self.__Mode.Text
                    pass
                elif (token.name == "noscript" and not self.__scripting):
                    _ = self.__createElement(token)
                    self.__switchModeTo(self.__Mode.InHeadNoscript)
                elif (token.name == "script"):
                    #TODO: Add support for JS.
                    pass
                elif (token.name == "template"):
                    #TODO: Handle case.
                    pass
                else: 
                    #Ignores "head" and any other tag.
                    pass

            elif (token.type == HTMLToken.TokenType.EndTag):
                if (token.name == "head"):
                    self.__removeCurrentFromOpenStack()
                    self.__switchModeTo(self.__Mode.AfterHead)
                elif (token.name in ["body", "html", "br"]):
                    self.__removeCurrentFromOpenStack()
                    self.__reconsumeIn(self.__Mode.AfterHead, token)
                elif (token.name == "template"):
                    #TODO: Handle case.
                    pass
            else:
                self.__removeCurrentFromOpenStack()
                self.__reconsumeIn(self.__Mode.AfterHead, token)


        def handleInHeadNoscript(token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
            if (token.type == HTMLToken.TokenType.DOCTYPE):
                pass
            elif (token.type == HTMLToken.TokenType.StartTag):
                token = cast(HTMLTag, token)
                if (token.name == "html"):
                    #TODO: Handle using the "in body".
                    pass
            elif (token.type == HTMLToken.TokenType.EndTag):
                token = cast(HTMLTag, token)
                if (token.name == "noscript"):
                    self.__removeCurrentFromOpenStack()
                    self.__switchModeTo(self.__Mode.InHead)
                elif (token.name == "br"):
                    self.__removeCurrentFromOpenStack()
                else:
                    pass
            elif (token.type == HTMLToken.TokenType.Character):
                if (charIsWhitespace(token.data)):
                    #TODO:Insert the character
                    pass
            elif (token.type == HTMLToken.TokenType.Comment):
                token = cast(HTMLCommentOrCharacter, token)
                comment = Comment(token.data)
                self.__currentElement.appendChild(comment)
            elif (token.type == HTMLToken.TokenType.StartTag):
                if (token.name in ["basefont", "bgsound", "link", "meta", "noframes", "style"]):
                    #TODO: Implement handling.
                    pass
                elif (token.name in ["head", "noscrip"]):
                    pass
            else:
                self.__removeCurrentFromOpenStack()


        def handleAfterHead(token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
            if (token.type == HTMLToken.TokenType.Character):
                if (charIsWhitespace(token.data)):
                    self.__insertCharacter(token)
            elif (token.type == HTMLToken.TokenType.Comment):
                self.__insertComment(token)
            elif (token.type == HTMLToken.TokenType.DOCTYPE):
                pass # Ignore token
            elif (token.type == HTMLToken.TokenType.StartTag):
                token = cast(HTMLTag, token)
                if (token.name == "html"):
                    #TODO: Handle using the "in body".
                    pass
                elif (token.name == "body"):
                    element = self.__createElement(token)
                    self.__openElements.append(element)
                    self.__switchModeTo(self.__Mode.InBody)
                elif (token.name == "frameset"):
                    pass # TODO: Handle case.
                elif (token.name in ["base", "basefont", "bgsound", "link", "meta", "noframes", "script", "style", "template", "title"]):
                    pass #TODO: Handle case.
                elif (token.name == "head"):
                    pass # Ignroe token.
            elif (token.type == HTMLToken.TokenType.EndTag):
                if (token.name == "template"):
                    pass #TODO: Handle case, Process the token using the rules for the "in head" insertion mode.
                elif (token.name in ["body", "html", "br"]):
                    token = HTMLTag(HTMLToken.TokenType.StartTag)
                    token.name = "body"
                    element = self.__createElement(token)
                    self.__addToOpenStack(element)
                    self.__framesetOK = False
                    self.__reconsumeIn(self.__Mode.InBody, token)
                else:
                    pass # Ignore token.
            else:
                token = HTMLTag(HTMLToken.TokenType.StartTag)
                token.name = "body"
                element = self.__createElement(token)
                self.__addToOpenStack(element)
                self.__reconsumeIn(self.__Mode.InBody, token)


        def handleInBody(token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
            if (token.type == HTMLToken.TokenType.Character):
                if (token.data is None):
                    pass #Ignore token.
                elif (CharacterData(token.data)):
                    #TODO: Reconstruct the active formatting elements, if any.
                    self.__insertCharacter(token)
                else:
                    #TODO: Reconstruct the active formatting elements, if any.
                    self.__insertCharacter(token)
                    self.__framesetOK = False
            elif (token.type == HTMLToken.TokenType.Comment):
                self.__insertComment(token)
            elif (token.type == HTMLToken.TokenType.DOCTYPE):
                pass # Ignore token.
            elif (token.type == HTMLToken.TokenType.StartTag):
                if (token.name == "html"):
                    pass # Handle case
                elif (token.name in ["base", "basefont", "bgsound", "link", "meta", "noframes", "script", "style", "template", "title"]):
                    pass # Handle case, Process the token using the rules for the "in head" insertion mode.
                elif (token.name == "body"):
                    pass # Handle case
                elif (token.name == "frameset"):
                    pass # Handle case
                elif (token.name in ["address", "article", "aside", "blockquote", "center", "details", "dialog", "dir", "div", "dl", "fieldset", "figcaption", "figure", "footer", "header", "hgroup", "main", "menu", "nav", "ol", "p", "section", "summary", "ul"]):
                    if (self.__currentElement.name == "p" and self.__currentElement.parentNode.name == "button"):
                        self.__removeCurrentFromOpenStack()
                        self.__createElement()

            elif (token.type == HTMLToken.TokenType.EndTag):
                if (token.name == "template"):
                    pass # Handle case, Process the token using the rules for the "in head" insertion mode.
                elif (token.name == "body"):
                    openBodyElement = filter(lambda element: element.name == "body", self.__openElements)
                    if (len(openBodyElement) == 0):
                        pass # Ignore token.
                        #TODO: handle the else case.
                    else:
                        self.__switchModeTo(self.__Mode.AfterBody)
                        #TODO: Implement the popping functionality.
                elif (token.name == "html"):
                    self.__reconsumeIn(self.__Mode.AfterBody, token)

            elif (token.type == HTMLToken.TokenType.EOF):
                pass #TODO: Handle case.



        def handleText(token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
            if (token.type == HTMLToken.TokenType.Character):
                self.__insertCharacter(token)
            elif (token.type == HTMLToken.TokenType.EOF):
                #TODO: Handle case
                pass
            elif (token.type == HTMLToken.TokenType.EndTag):
                if(token.name == "script"):
                    #TODO: handle case
                    pass
            else:
                self.__removeCurrentFromOpenStack()
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

        def handleAfterBody() -> None:
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

