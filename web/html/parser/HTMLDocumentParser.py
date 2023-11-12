from enum import Enum, Flag, auto
from os import name
from typing import Any, List, Union, Callable, cast, Optional
from web.dom.elements.HTMLScriptElement import HTMLScriptElement
from web.dom.elements.HTMLTemplateElement import HTMLTemplateElement
from web.html.parser.ListOfActiveElements import ListOfActiveElements
from web.html.parser.StackOfOpenElements import StackOfOpenElements
from web.dom.elements.Comment import Comment
from web.html.parser.utils import charIsWhitespace, tagIsSpecial
from web.dom.elements.Element import Element
from web.dom.Document import Document
from web.dom.Node import Node
from web.dom.elements.Text import Text
from web.dom.DocumentType import DocumentType
from web.html.parser.HTMLToken import HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter
from web.html.parser.HTMLTokenizer import HTMLTokenizer, DEBUG
from web.dom.ElementFactory import ElementFactory
from dataclasses import dataclass
from copy import deepcopy
from browser.utils.logging import log

class HTMLDocumentParser:
    @dataclass
    class AdjustedInsertionLocation:
        parent: Union[Element, None] = None
        insert_before_sibling: Union[Element, None] = None  # If none insert as last child.

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
        self.__current_insertion_mode = self.__Mode.Initial
        self.__original_insertion_mode: Union[HTMLDocumentParser.__Mode, None] = None
        self.__open_elements = StackOfOpenElements()
        self.__tokenizer = HTMLTokenizer(html, self.__token_handler)
        self.__document = Document()
        self.__document_node = None
        self.__scripting: bool = False
        self.__frameset_ok: bool = True
        self.__formatting_elements = ListOfActiveElements()
        self.__foster_parenting: bool = False
        self.parsing_fragment: bool = False
        self.invokef_while_document_write: bool = False
        self.__form_element: Union[Element, None] = None
        self.__notify_cb: Union[Callable, None] = None

    @property
    def __current_element(self) -> Node:
        """
        Gets the latest opened element aka "parent".
        """
        return self.__document_node if self.__open_elements.isEmpty() else self.__open_elements.last()

    def run(self, cb: Callable) -> None:
        self.__notify_cb = cb
        self.__tokenizer.run()

    def __token_handler(self, token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:

        if DEBUG:
            log("Token: ", token)
            log("Input mode: ", self.__current_insertion_mode)
            log("self.__open_elements")
            log("Elements: ", self.__open_elements.elements())

        switcher = self.__get_mode_switcher()
        if switcher is not None:
            switcher(token)

        if token.type == HTMLToken.TokenType.EOF:
            if self.__notify_cb:
                self.__notify_cb(self.__document_node)

    def __continue_in(self, mode: __Mode) -> None:
        self.__switchModeTo(mode)

    def __switchModeTo(self, newMode: __Mode) -> None:
        """
        Switch state and consume next character.
        """
        self.__current_insertion_mode = newMode

    def __reconsumeIn(self,
                      newMode: __Mode,
                      token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
        """
        Switch state without consuming next character.
        """
        self.__current_insertion_mode = newMode
        switcher = self.__get_mode_switcher()
        if switcher is not None:
            switcher(token)

    def __create_element(self, token: HTMLTag) -> Element:
        """
        Creates element based on given token and sets parent for it.
        """
        parent = self.__current_element
        log("Token:", token)
        element = ElementFactory.create_element(token, parent, self.__document)
        element.parentNode.appendChild(element)

        return element

    def __create_element_with_adjusted_location(self,
                                                token: HTMLTag,
                                                adjusted_location: AdjustedInsertionLocation) -> Optional[Element]:
        """
        Creates element based on given token and inserts it based on adjsuted location.
        """
        parent = adjusted_location.parent
        element = ElementFactory.create_element(token, parent, self.__document)
        if adjusted_location.insert_before_sibling is None:
            element.parentNode.appendChild(element)
        else:
            element.parentNode.appendChildBeforeElement(adjusted_location.insert_before_sibling)

        return element

    def __insert_character(self, token: HTMLCommentOrCharacter) -> None:
        if type(self.__current_element) is Document:
            return
        elif len(self.__current_element.children) > 0 and type(self.__current_element.children[-1]) is Text:
            cast(Text, self.__current_element.children[-1]).appendData(token.data)
        else:
            text_node = Text(self.__document, self.__current_element, token.data)
            text_node.parentNode = self.__current_element
            self.__current_element.appendChild(text_node)

    def __insert_comment(self, token: HTMLCommentOrCharacter) -> None:
        comment = Comment(token.data, self.__current_element, self.__document)
        comment.parentNode = self.__current_element
        self.__current_element.appendChild(comment)

    def __adoption_agency_algorithm(self, token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
        subject = token.name
        if self.__current_element.name == subject and not self.__formatting_elements.contains(self.__current_element):
            self.__open_elements.pop()
            return
        outer_loop_counter = 0

        while outer_loop_counter < 8:
            outer_loop_counter += 1
            formatting_element_result = self.__formatting_elements.lastElementWithTagNameBeforeMarker(subject)
            if formatting_element_result is None:
                return
            formatting_element = formatting_element_result.element

            if not self.__open_elements.containsElement(formatting_element):
                self.__formatting_elements.remove(formatting_element)
                return
            if self.__open_elements.containsElement(formatting_element) and not self.__open_elements.hasInScope():
                return
            if formatting_element != self.__current_element:
                # TODO: Handle parsing error.
                pass

            further_most_block = self.__open_elements.topmostSpecialNodeBelow(formatting_element)

            if further_most_block is None:
                self.__open_elements.popUntilElementWithAtagNameHasBeenPopped(formatting_element.name)
                self.__formatting_elements.remove(formatting_element)
                return

            """ commonAncestor = self.__open_elements.elementBefore(formatting_element)
            bookMark = formatting_element_result.index

            node = deepcopy(further_most_block.element)
            lastNode = deepcopy(further_most_block.element)
            innerLoopCounter = 0
            while (innerLoopCounter <= 3):
                node = self.__open_elements.elementBefore(node)
                if (node is None):
                    node = self.__open_elements.getElementOnIndex(fur) """

        # bookmark =
        # case 13
        # TODO: Continue here https://html.spec.whatwg.org/multipage/parsing.html#adoption-agency-algorithm
        # https://html.spec.whatwg.org/multipage/parsing.html#has-an-element-in-scope

    def __generate_implied_end_tags(self, exception: Optional[str] = None) -> None:
        while (self.__current_element.name != exception and self.__current_element.name in ["caption", "colgroup", "dd",
                                                                                        "dt", "li", "optgroup",
                                                                                        "option", "p", "rb", "rp", "rt",
                                                                                        "rtc", "tbody", "td", "tfoot",
                                                                                        "th", "thead", "tr"]):
            self.__open_elements.pop()

    def __reconstruct_the_active_formatting_elements(self) -> None:
        if self.__formatting_elements.isEmpty():
            return

        entry = self.__formatting_elements.lastEntry()
        if entry.isMarker or entry.element.name == self.__open_elements.contains(entry.element.name):
            return

        def rewind(entry: ListOfActiveElements.Entry) -> Optional[ListOfActiveElements.Entry]:
            return self.__formatting_elements.entryBefore(entry)


        if len(self.__formatting_elements.entries()) > 1:
            entry = rewind(entry)
            while entry and entry.isMarker is False and self.__open_elements.contains(entry.element.name) is False:
                entry = rewind(entry)
            entry = self.__formatting_elements.entryAfter(entry)


    def __close_ap_element(self) -> None:
        self.__generate_implied_end_tags("p")
        if self.__current_element.name != "p":
            # TODO: Handle parse error.
            pass
        self.__open_elements.popUntilElementWithAtagNameHasBeenPopped("p")

    def __find_appropriate_place_for_inserting_node(self) -> AdjustedInsertionLocation:
        target = self.__current_element
        adjusted_location = self.AdjustedInsertionLocation()

        if self.__foster_parenting and target.name in ["table", "tbody", "tfoot", "thead", "tr"]:
            template_result = self.__open_elements.lastElementWithTagName("template")
            table_result = self.__open_elements.lastElementWithTagName("table")
            if (template_result is not None and table_result is None or (
                    table_result is not None and table_result.index < template_result.index)):
                adjusted_location.parent = template_result.element
                adjusted_location.insert_before_sibling = None
                return adjusted_location
            elif table_result is None:
                adjusted_location.parent = self.__open_elements.first()
                adjusted_location.insert_before_sibling = None
                return adjusted_location
            elif table_result is not None and table_result.element.parentNode is not None:
                adjusted_location.parent = table_result.element.parentNode
                adjusted_location.insert_before_sibling = table_result.element
                return adjusted_location

            previous_element = self.__open_elements.elementBefore(table_result.element)
            adjusted_location.parent = previous_element
            adjusted_location.insert_before_sibling = None
            return adjusted_location
        else:
            adjusted_location.parent = target
            adjusted_location.insert_before_sibling = None

        if adjusted_location.parent.name == "template":
            adjusted_location.parent = cast(HTMLTemplateElement, adjusted_location.parent).content
            adjusted_location.insert_before_sibling = None

        return adjusted_location

    def handle_initial(self, token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
        if token.type == HTMLToken.TokenType.DOCTYPE:
            token = cast(HTMLDoctype, token)
            documentNode = DocumentType(token, self.__document)
            self.__document_node = documentNode
            # TODO: Handle quircks mode.
            self.__switchModeTo(self.__Mode.BeforeHTML)

    def handle_before_html(self, token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
        if token.type == HTMLToken.TokenType.StartTag:
            token = cast(HTMLTag, token)
            if token.name == "html":
                element = self.__create_element(token)
                self.__open_elements.push(element)
                self.__switchModeTo(self.__Mode.BeforeHead)
            else:
                token = HTMLTag(HTMLToken.TokenType.StartTag)
                token.name = "html"
                element = self.__create_element(token)
                self.__open_elements.push(element)
                self.__switchModeTo(self.__Mode.BeforeHead)

    def handle_before_head(self, token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
        log("handle_before_head")
        if token.type == HTMLToken.TokenType.Character:
            if charIsWhitespace(token.data):
                self.__continue_in(self.__Mode.BeforeHead)
        elif token.type == HTMLToken.TokenType.Comment:
            self.__insert_comment(token)
        elif token.type == HTMLToken.TokenType.DOCTYPE:
            self.__continue_in(self.__Mode.BeforeHead)
        elif token.type == HTMLToken.TokenType.StartTag:
            token = cast(HTMLTag, token)
            if token.name == "head":
                element = self.__create_element(token)
                self.__open_elements.push(element)
                self.__switchModeTo(self.__Mode.InHead)
        else:
            token = HTMLTag(HTMLToken.TokenType.StartTag)
            token.name = "head"
            element = self.__create_element(token)
            self.__open_elements.push(element)
            self.__switchModeTo(self.__Mode.InHead)

    def handle_in_head(self, token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
        if token.type == HTMLToken.TokenType.Character:
            if charIsWhitespace(token.data):
                self.__insert_character(token)
        elif token.type == HTMLToken.TokenType.Comment:
            token = cast(HTMLCommentOrCharacter, token)
            comment = Comment(token.data, self.__current_element, self.__document)
            self.__current_element.appendChild(comment)
        elif token.type == HTMLToken.TokenType.DOCTYPE:
            pass
        elif token.type == HTMLToken.TokenType.StartTag:
            token = cast(HTMLTag, token)
            if token.name == "html":
                # TODO: Handle using the "in body"
                raise NotImplementedError
            elif token.name in ["base", "basefont", "bgsound", "link"]:
                # This kind of elements are not added to open stack.
                _ = self.__create_element(token)
            elif token.name == "meta":
                # This kind of elements are not added to open stack.
                element = self.__create_element(token)
                if "charset" in element.attributes:
                    # TODO: Handle charset attribute.
                    pass

            elif token.name == "title":
                element = self.__create_element(token)
                self.__open_elements.push(element)
                self.__tokenizer.switch_state_to(
                    self.__tokenizer.State.RCDATA)
                log("Assigning insertion mode:", self.__current_insertion_mode)
                self.__original_insertion_mode = self.__current_insertion_mode
                self.__switchModeTo(self.__Mode.Text)
            elif (token.name == "noscript" and self.__scripting) or (token.name in ["noframes", "style"]):
                element = self.__create_element(token)
                self.__open_elements.push(element)
                self.__tokenizer.switch_state_to(
                    self.__tokenizer.State.RAWTEXT)
                self.__original_insertion_mode = self.__current_insertion_mode
                self.__switchModeTo(self.__Mode.Text)
            elif token.name == "noscript" and not self.__scripting:
                element = self.__create_element(token)
                self.__open_elements.push(element)
                self.__switchModeTo(self.__Mode.InHeadNoscript)
            elif token.name == "script":
                # TODO: Add support for JS.
                adjusted_insertion_location = self.__find_appropriate_place_for_inserting_node()
                element = cast(HTMLScriptElement,
                               self.__create_element_with_adjusted_location(token, adjusted_insertion_location))
                element.parserDocument = self.__document
                element.isNonBlocking = False

                if self.parsing_fragment:
                    raise NotImplementedError
                if self.invokef_while_document_write:
                    raise NotImplementedError

                self.__open_elements.push(element)
                self.__tokenizer.switch_state_to(self.__tokenizer.State.ScriptData)
                self.__original_insertion_mode = self.__current_insertion_mode
                self.__switchModeTo(self.__Mode.Text)

            elif token.name == "template":
                element = self.__create_element(token)
                self.__open_elements.push(element)
                self.__formatting_elements.addMarker()
                self.__frameset_ok = False
                # self.__switchModeTo(self.__Mode.InTemplate)
                # TODO: Handle rest of the case.
            else:
                # Ignores "head" and any other tag.
                pass

        elif token.type == HTMLToken.TokenType.EndTag:
            if token.name == "head":
                log("removing head")
                log(self.__open_elements.elements())
                self.__open_elements.popUntilElementWithAtagNameHasBeenPopped(token.name)
                self.__switchModeTo(self.__Mode.AfterHead)
            elif token.name in ["body", "html", "br"]:
                self.__open_elements.pop()
                self.__reconsumeIn(self.__Mode.AfterHead, token)
            elif token.name == "template":
                if not self.__open_elements.contains("template"):
                    pass
                else:
                    self.__open_elements.popUntilElementWithAtagNameHasBeenPopped("template")
                    self.__formatting_elements.clearUpToTheLastMarker()
                # TODO: Handle rest of the case.
        else:
            self.__open_elements.pop()
            self.__reconsumeIn(self.__Mode.AfterHead, token)

    def handle_in_head_noscript(self, token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
        if token.type == HTMLToken.TokenType.DOCTYPE:
            pass
        elif token.type == HTMLToken.TokenType.EndTag:
            token = cast(HTMLTag, token)
            if token.name == "noscript":
                log("removing noscript")
                log(self.__open_elements.elements())
                self.__open_elements.pop()
                self.__switchModeTo(self.__Mode.InHead)
            elif token.name == "br":
                self.__open_elements.pop()
            else:
                pass
        elif token.type == HTMLToken.TokenType.Character:
            if charIsWhitespace(token.data):
                self.__insert_character(token)
            else:
                self.__insert_character(token)
        elif token.type == HTMLToken.TokenType.Comment:
            token = cast(HTMLCommentOrCharacter, token)
            comment = Comment(token.data, self.__current_element, self.__document)
            self.__current_element.appendChild(comment)
        elif token.type == HTMLToken.TokenType.StartTag:
            if token.name in ["basefont", "bgsound", "link", "noframes", "style"]:
                element = self.__create_element(token)
                self.__open_elements.push(element)
            elif token.name in ["meta"]:
                pass
            elif token.name in ["head", "noscript"]:
                pass
            elif token.name == "html":
                # TODO: Handle using the "in body".
                raise NotImplementedError
        else:
            self.__open_elements.pop()
            self.__current_element = self.__open_elements.lastElementWithTagName("head")
            self.__switchModeTo(self.__Mode.InHead)

    def handle_after_head(self, token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
        log("handle_after_head", token)
        if token.type == HTMLToken.TokenType.Character:
            if charIsWhitespace(token.data):
                self.__insert_character(token)
        elif token.type == HTMLToken.TokenType.Comment:
            self.__insert_comment(token)
        elif token.type == HTMLToken.TokenType.DOCTYPE:
            pass  # Ignore token
        elif token.type == HTMLToken.TokenType.StartTag:
            token = cast(HTMLTag, token)
            if token.name == "html":
                # TODO: Handle using the "in body".
                raise NotImplementedError
            elif token.name == "body":
                log("Yes here")
                log(self.__open_elements.elements())
                element = self.__create_element(token)
                self.__open_elements.push(element)
                self.__switchModeTo(self.__Mode.InBody)
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
                element = self.__create_element(_token)
                self.__open_elements.push(element)
                self.__frameset_ok = False
                self.__reconsumeIn(self.__Mode.InBody, token)
            else:
                pass  # Ignore token.
        else:
            _token = HTMLTag(HTMLToken.TokenType.StartTag)
            _token.name = "body"
            element = self.__create_element(_token)
            self.__open_elements.push(element)
            self.__reconsumeIn(self.__Mode.InBody, token)

    def handle_in_body(self, token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
        if token.type == HTMLToken.TokenType.Character:
            if token.data is None:
                pass  # Ignore token.
            elif charIsWhitespace(token.data):
                # TODO: Reconstruct the active formatting elements, if any.
                self.__insert_character(token)
            else:
                # TODO: Reconstruct the active formatting elements, if any.
                self.__insert_character(token)
                self.__frameset_ok = False
        elif token.type == HTMLToken.TokenType.Comment:
            self.__insert_comment(token)
        elif token.type == HTMLToken.TokenType.DOCTYPE:
            pass  # Ignore token.
        elif token.type == HTMLToken.TokenType.StartTag:
            if token.name == "html":
                raise NotImplementedError  # Handle case
            elif token.name == "template":
                # Handle case, Process the token using the rules for the "in head" insertion mode.
                raise NotImplementedError
            elif token.name in ["noframes", "style"]:
                element = self.__create_element(token)
                self.__open_elements.push(element)
                self.__tokenizer.switch_state_to(
                    self.__tokenizer.State.RAWTEXT)
                self.__original_insertion_mode = self.__current_insertion_mode
                self.__switchModeTo(self.__Mode.Text)
            elif token.name in ["base", "basefont", "bgsound", "link"]:
                # This kind of elements are not added to open stack.
                _ = self.__create_element(token)
            elif token.name == "meta":
                # This kind of elements are not added to open stack.
                element = self.__create_element(token)
                if "charset" in element.attributes:
                    # TODO: Handle charset attribute.
                    pass
            elif token.name == "title":
                element = self.__create_element(token)
                self.__open_elements.push(element)
                self.__tokenizer.switch_state_to(
                    self.__tokenizer.State.RCDATA)
                self.__original_insertion_mode = self.__current_insertion_mode
                self.__switchModeTo(self.__Mode.Text)
            elif token.name == "script":
                # TODO: Add support for JS.
                adjustedInsertionLocation = self.__find_appropriate_place_for_inserting_node()
                element = cast(HTMLScriptElement,
                               self.__create_element_with_adjusted_location(token, adjustedInsertionLocation))
                element.parserDocument = self.__document
                element.isNonBlocking = False

                if self.parsing_fragment:
                    raise NotImplementedError
                if self.invokef_while_document_write:
                    raise NotImplementedError

                self.__open_elements.push(element)
                self.__tokenizer.switch_state_to(self.__tokenizer.State.ScriptData)
                self.__original_insertion_mode = self.__current_insertion_mode
                self.__switchModeTo(self.__Mode.Text)
            elif token.name == "body":
                # TODO: handle parse error.
                pass
            elif token.name == "frameset":
                raise NotImplementedError  # Handle case
            elif (token.name in ["address", "article", "aside", "blockquote", "center", "details", "dialog", "dir",
                                 "div", "dl", "fieldset", "figcaption", "figure", "footer", "header", "hgroup",
                                 "main", "menu", "nav", "ol", "p", "section", "summary", "ul"]):
                if self.__open_elements.hasInButtonScope("p"):
                    self.__open_elements.pop()
                element = self.__create_element(token)
                self.__open_elements.push(element)
            elif token.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                if self.__open_elements.hasInButtonScope("p"):
                    self.__open_elements.pop()
                elif self.__current_element.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                    self.__open_elements.pop()
                element = self.__create_element(token)
                self.__open_elements.push(element)
            elif token.name in ["pre", "listing"]:
                if self.__open_elements.hasInButtonScope("p"):
                    self.__open_elements.pop()
                element = self.__create_element(token)
                self.__open_elements.push(element)
                # TODO: Handle new line
                self.__frameset_ok = False
            elif token.name == "form":
                if self.__form_element is not None and self.__open_elements.contains("template") is False:
                    # TODO: Handle parse error.
                    pass
                elif self.__open_elements.hasInButtonScope("p"):
                    self.__open_elements.popUntilElementWithAtagNameHasBeenPopped("p")

                element = self.__create_element(token)
                self.__open_elements.push(element)

                if self.__open_elements.contains("template") is False:
                    self.__form_element = element
            elif token.name == "li":
                self.__frameset_ok = False

                for element in reversed(self.__open_elements.elements()):
                    node = element
                    if self.__current_element.name == "li":
                        self.__generate_implied_end_tags("li")
                        if self.__current_element.name == "li":
                            # TODO: Handle parse error
                            pass
                        self.__open_elements.popUntilElementWithAtagNameHasBeenPopped("li")
                        break

                    if tagIsSpecial(node.name) and node.name not in ["address", "div", "p"]:
                        break

                if self.__open_elements.hasInButtonScope("p"):
                    self.__close_ap_element()

                element = self.__create_element(token)
                self.__open_elements.push(element)

            elif token.name in ["dd", "dt"]:
                log(token.name)
                self.__frameset_ok = False
                element = self.__create_element(token)
                self.__open_elements.push(element)
                #if token.name == "dd":
                # TODO: Handle the case properly
                #raise NotImplementedError
            elif token.name == "plaintext":
                if self.__open_elements.hasInButtonScope("p"):
                    self.__open_elements.pop()
                element = self.__create_element(token)
                self.__open_elements.push(element)
                self.__tokenizer.switch_state_to(
                    self.__tokenizer.State.PLAINTEXT)
            elif token.name == "button":
                if self.__open_elements.hasInScope(token.name):
                    self.__open_elements.popUntilElementWithAtagNameHasBeenPopped(token.name)
                # TODO: Reconstruct the active formatting elements, if any.
                self.__frameset_ok = False
                element = self.__create_element(token)
                self.__open_elements.push(element)
            elif token.name == "a":
                if self.__open_elements.hasInScope(token.name):
                    self.__open_elements.popUntilElementWithAtagNameHasBeenPopped(token.name)

                element = self.__create_element(token)
                self.__open_elements.push(element)
            elif (token.name in ["b", "big", "code", "em", "font", "i", "s", "small", "strike", "strong", "tt",
                                 "u"]):
                # TODO: Reconstruct the active formatting elements, if any and add handling to all tother places too
                element = self.__create_element(token)
                self.__open_elements.push(element)
            elif token.name == "nobr":
                if self.__open_elements.hasInScope(token.name):
                    # TODO: run the adoption agency algorithm for the token
                    raise NotImplementedError
                self.__create_element(token)
            # TODO: Push onto the list of active formatting elements that element. Add this handling to other places too.
            elif token.name in ["area", "br", "embed", "img", "keygen", "wbr"]:
                # TODO: Construct active elements.
                element = self.__create_element(token)
                self.__open_elements.push(element)
                self.__open_elements.pop()
            elif token.name == "input":
               self.__create_element(token)
            elif token.name == "textarea":
                element = self.__create_element(token)
                self.__open_elements.push(element)
                # TODO: Handle new line
                self.__tokenizer.switch_state_to(self.__tokenizer.State.RCDATA)
                self.__original_insertion_mode = self.__current_insertion_mode
                self.__frameset_ok = False
                self.__switchModeTo(self.__Mode.Text)
            else:
                # TODO: Construct active elements.
                element = self.__create_element(token)
                self.__open_elements.push(element)
        elif token.type == HTMLToken.TokenType.EndTag:
            if token.name == "template":
                # Handle case, Process the token using the rules for the "in head" insertion mode.
                raise NotImplementedError
            elif token.name == "body":
                log("Closing body element")
                open_body_element = self.__open_elements.lastElementWithTagName(token.name)
                if open_body_element is None:
                    log("No body tag in open stack")
                    pass  # Ignore token.
                # TODO: handle the else case.
                else:
                    self.__switchModeTo(self.__Mode.AfterBody)
                    self.__open_elements.popUntilElementWithAtagNameHasBeenPopped(token.name)
                    # TODO: Implement the popping functionality.
                    self.__switchModeTo(self.__Mode.AfterBody)
            elif token.name == "html":
                self.__reconsumeIn(self.__Mode.AfterBody, token)
            elif (token.name in ["address", "article", "aside", "blockquote", "button", "center", "details",
                                 "dialog", "dir", "div", "dl", "fieldset", "figcaption", "figure", "footer",
                                 "header", "hgroup", "listing", "main", "menu", "nav", "ol", "pre", "section",
                                 "summary", "ul"]):
                if not self.__open_elements.hasInScope(token.name):
                    pass
                else:
                    # TODO: Generate implied end tags
                    if not self.__open_elements.currentNode().name == token.name:
                        # TODO: Handle parse error
                        pass

                    self.__open_elements.popUntilElementWithAtagNameHasBeenPopped(token.name)
            elif token.name == "form":
                if self.__open_elements.contains("template") is False:
                    node = self.__form_element
                    self.__form_element = None
                    if node is None or self.__open_elements.hasInScope(node.name) is False:
                        # TODO: Handle parse error.
                        return
                    self.__generate_implied_end_tags()
                    if self.__current_element != node:
                        # TODO: Handle parse error
                        pass
                    self.__open_elements.popUntilElementWithAtagNameHasBeenPopped(node.name)
                else:
                    if self.__open_elements.hasInScope("form"):
                        # TODO: Handle parse error.
                        return
                    self.__generate_implied_end_tags()
                    if self.__current_element.name != "form":
                        # TODO: Handle parse error
                        pass
                    self.__open_elements.popUntilElementWithAtagNameHasBeenPopped("form")

            elif token.name == "p":
                if not self.__open_elements.hasInButtonScope("p"):
                    element = self.__create_element(token)
                    self.__open_elements.push(element)
                self.__open_elements.pop()
            elif token.name == "li":
                if not self.__open_elements.hasInListItemScope(token.name):
                    # TODO: Handle parse rror.
                    return

                self.__generate_implied_end_tags(token.name)
                if self.__current_element.name != "li":
                    # TODO: Handle parse error.
                    pass
                log("Removing 'li'")
                self.__open_elements.popUntilElementWithAtagNameHasBeenPopped("li")
            elif token.name in ["dd", "dt"]:
                if not self.__open_elements.hasInScope(token.name):
                    raise NotImplementedError  # TODO: handle parse error.

                if self.__current_element.name != token.name:
                    raise NotImplementedError  # TODO: handle parse error.

                while not self.__open_elements.isEmpty():
                    poppedElement = self.__open_elements.pop()
                    if poppedElement.name == token.name:
                        break
                return
            elif token.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                if not self.__open_elements.hasInScope(token.name):
                    raise NotImplementedError  # TODO: handle parse error.
                    return

                if self.__current_element.name != token.name:
                    raise NotImplementedError  # TODO: handle parse error.

                while not self.__open_elements.isEmpty():
                    poppedElement = self.__open_elements.pop()
                    if poppedElement.name == token.name:
                        break
                return
            elif token.name == "sarcasm":
                # TODO: Handle case
                raise NotImplementedError
            elif (token.name in ["a", "b", "big", "code", "em", "font", "i", "nobr", "s", "small", "strike",
                                 "strong", "tt", "u"]):
                # TODO: Run the adoption agency algorithm for the token.
                self.__adoption_agency_algorithm(token)
            else:

                for element in reversed(self.__open_elements.elements()):
                    node = element
                    if node.name == token.name:
                        self.__generate_implied_end_tags(token.name)
                        if node != self.__current_element:
                            # TODO: Handle parse error.
                            pass

                        while self.__current_element.name != node.name:
                            self.__open_elements.pop()

                        self.__open_elements.pop()
                        break

                    if tagIsSpecial(node.name):
                        # TODO: Handle parse error.
                        return

        elif token.type == HTMLToken.TokenType.EOF:
            for node in self.__open_elements.elements():
                if node.name not in ["dd", "dt", "li", "optgroup", "option", "p", "rb", "rp", "rt", "rtc", "tbody",
                                     "td", "tfoot", "th", "thead", "tr", "body", "html"]:
                    # TODO: Handle parse error.
                    raise NotImplementedError()

            # TODO: This is a hack, check if valid
            self.__open_elements.popUntilElementWithAtagNameHasBeenPopped("body")
            # TODO: Implement the popping functionality.
            self.__reconsumeIn(self.__Mode.AfterBody, token)

            return

    def handle_text(self, token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
        if token.type == HTMLToken.TokenType.Character:
            self.__insert_character(token)
        elif token.type == HTMLToken.TokenType.EOF:
            if self.__current_element.name == "script":
                # TODO: Mark the script element as "already started".
                pass
            self.__open_elements.pop()
            if self.__original_insertion_mode is not None:
                self.__reconsumeIn(self.__original_insertion_mode, token)
        elif token.type == HTMLToken.TokenType.EndTag and token.name == "script":
            # TODO: flush_character_insertions()
            script = self.__current_element
            self.__open_elements.pop()
            if self.__original_insertion_mode is not None:
                self.__switchModeTo(self.__original_insertion_mode)
        # TODO: HAndle rest of the case.
        else:
            self.__open_elements.pop()
            if self.__original_insertion_mode is not None:
                self.__switchModeTo(self.__original_insertion_mode)

    def handle_in_table(self) -> None:
        return

    def handle_in_table_text(self) -> None:
        return

    def handle_in_caption(self) -> None:
        return

    def handle_in_column_group(self) -> None:
        return

    def handle_in_table_body(self) -> None:
        return

    def handle_in_row(self) -> None:
        return

    def handle_in_cell(self) -> None:
        return

    def handle_in_select(self) -> None:
        return

    def handle_in_select_in_table(self) -> None:
        return

    def handle_in_template(self) -> None:
        return

    def handle_after_body(self, token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
        if token.type == HTMLToken.TokenType.EOF:
            self.__open_elements.popAllElements()
        return

    def handle_in_frameset(self) -> None:
        return

    def handle_after_frameset(self) -> None:
        return

    def handle_after_after_body(self) -> None:
        return

    def handle_after_after_frameset(self) -> None:
        return

    def __get_mode_switcher(self) -> Optional[Any]:  # TODO: Check typing

        switcher = {
            self.__Mode.Initial: self.handle_initial,
            self.__Mode.BeforeHTML: self.handle_before_html,
            self.__Mode.BeforeHead: self.handle_before_head,
            self.__Mode.InHead: self.handle_in_head,
            self.__Mode.InHeadNoscript: self.handle_in_head_noscript,
            self.__Mode.AfterHead: self.handle_after_head,
            self.__Mode.InBody: self.handle_in_body,
            self.__Mode.Text: self.handle_text,
            self.__Mode.InTable: self.handle_in_table,
            self.__Mode.InTableText: self.handle_in_table_text,
            self.__Mode.InCaption: self.handle_in_caption,
            self.__Mode.InColumnGroup: self.handle_in_column_group,
            self.__Mode.InTableBody: self.handle_in_table_body,
            self.__Mode.InRow: self.handle_in_row,
            self.__Mode.InCell: self.handle_in_cell,
            self.__Mode.InSelect: self.handle_in_select,
            self.__Mode.InSelectInTable: self.handle_in_select_in_table,
            self.__Mode.InTemplate: self.handle_in_template,
            self.__Mode.AfterBody: self.handle_after_body,
            self.__Mode.InFrameset: self.handle_in_frameset,
            self.__Mode.AfterFrameset: self.handle_after_frameset,
            self.__Mode.AfterAfterBody: self.handle_after_after_body,
            self.__Mode.AfterAfterFrameset: self.handle_after_after_frameset,
        }

        return switcher.get(self.__current_insertion_mode)

    def current_insertion_mode(self) -> __Mode:
        return self.__current_insertion_mode
