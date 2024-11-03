from enum import Enum, Flag, auto
from os import name
from typing import Any, List, Union, Callable, cast, Optional
from web.dom.elements.HTMLScriptElement import HTMLScriptElement
from web.dom.elements.HTMLTemplateElement import HTMLTemplateElement
from web.html.parser.ListOfActiveElements import ListOfActiveElements
from web.html.parser.StackOfOpenElements import StackOfOpenElements
from web.dom.elements.Comment import Comment
from web.html.parser.utils import tag_is_special
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
        self._current_insertion_mode = self._Mode.Initial
        self._original_insertion_mode: Union[HTMLDocumentParser._Mode, None] = None
        self._open_elements = StackOfOpenElements()
        self._tokenizer = HTMLTokenizer(html, self._token_handler)
        self._document = Document()
        self._document_node = None
        self._scripting: bool = False
        self._frameset_ok: bool = True
        self._formatting_elements = ListOfActiveElements()
        self._foster_parenting: bool = False
        self.parsing_fragment: bool = False
        self.invokef_while_document_write: bool = False
        self._form_element: Union[Element, None] = None
        self._notify_cb: Union[Callable, None] = None

    @property
    def _current_element(self) -> Node:
        """
        Gets the latest opened element aka "parent".
        """
        return self._document_node if self._open_elements.is_empty() else self._open_elements.last()

    def run(self, cb: Callable) -> None:
        self._notify_cb = cb
        self._tokenizer.run()

    def _token_handler(self, token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:

        if DEBUG:
            log("Token: ", token)
            log("Input mode: ", self._current_insertion_mode)
            log("self._open_elements")
            log("Elements: ", self._open_elements.elements())

        switcher = self._get_mode_switcher()
        if switcher is not None:
            switcher(token)

        if token.type == HTMLToken.TokenType.EOF:
            if self._notify_cb:
                self._notify_cb(self._document_node)

    def _continue_in(self, mode: _Mode) -> None:
        self._switchModeTo(mode)

    def _switchModeTo(self, new_mode: _Mode) -> None:
        """
        Switch state and consume next character.
        """
        self._current_insertion_mode = new_mode

    def _reconsumeIn(self,
                      new_mode: _Mode,
                      token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
        """
        Switch state without consuming next character.
        """
        self._current_insertion_mode = new_mode
        switcher = self._get_mode_switcher()
        if switcher is not None:
            switcher(token)

    def _create_element(self, token: HTMLTag) -> Element:
        """
        Creates element based on given token and sets parent for it.
        """
        parent = self._current_element
        log("Token:", token)
        element = ElementFactory.create_element(token, parent, self._document)
        element.parentNode.appendChild(element)

        return element

    def _create_element_with_adjusted_location(self,
                                                token: HTMLTag,
                                                adjusted_location: AdjustedInsertionLocation) -> Optional[Element]:
        """
        Creates element based on given token and inserts it based on adjusted location.
        """
        parent = adjusted_location.parent
        element = ElementFactory.create_element(token, parent, self._document)
        if adjusted_location.insert_before_sibling is None:
            element.parentNode.appendChild(element)
        else:
            element.parentNode.appendChildBeforeElement(adjusted_location.insert_before_sibling)

        return element

    def _insert_character(self, token: HTMLCommentOrCharacter) -> None:
        if type(self._current_element) is Document:
            return
        elif len(self._current_element.children) > 0 and type(self._current_element.children[-1]) is Text:
            cast(Text, self._current_element.children[-1]).appendData(token.data)
        else:
            text_node = Text(self._document, self._current_element, token.data)
            text_node.parentNode = self._current_element
            self._current_element.appendChild(text_node)

    def _insert_comment(self, token: HTMLCommentOrCharacter) -> None:
        comment = Comment(token.data, self._current_element, self._document)
        comment.parentNode = self._current_element
        self._current_element.appendChild(comment)

    def _adoption_agency_algorithm(self, token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
        subject = token.name
        if self._current_element.name == subject and not self._formatting_elements.contains(self._current_element):
            self._open_elements.pop()
            return
        outer_loop_counter = 0

        while outer_loop_counter < 8:
            outer_loop_counter += 1
            formatting_element_result = self._formatting_elements.lastElementWithTagNameBeforeMarker(subject)
            if formatting_element_result is None:
                return
            formatting_element = formatting_element_result.element

            if not self._open_elements.contains_element(formatting_element):
                self._formatting_elements.remove(formatting_element)
                return
            if self._open_elements.contains_element(formatting_element) and not self._open_elements.has_in_scope():
                return
            if formatting_element != self._current_element:
                # TODO: Handle parsing error.
                pass

            further_most_block = self._open_elements.topmost_special_node_below(formatting_element)

            if further_most_block is None:
                self._open_elements.pop_until_element_with_tag_name_has_been_popped(formatting_element.name)
                self._formatting_elements.remove(formatting_element)
                return

            """ commonAncestor = self._open_elements.elementBefore(formatting_element)
            bookMark = formatting_element_result.index

            node = deepcopy(further_most_block.element)
            lastNode = deepcopy(further_most_block.element)
            innerLoopCounter = 0
            while (innerLoopCounter <= 3):
                node = self._open_elements.elementBefore(node)
                if (node is None):
                    node = self._open_elements.getElementOnIndex(fur) """

        # bookmark =
        # case 13
        # TODO: Continue here https://html.spec.whatwg.org/multipage/parsing.html#adoption-agency-algorithm
        # https://html.spec.whatwg.org/multipage/parsing.html#has-an-element-in-scope

    def _generate_implied_end_tags(self, exception: Optional[str] = None) -> None:
        while (self._current_element.name != exception and self._current_element.name in ["caption", "colgroup", "dd",
                                                                                        "dt", "li", "optgroup",
                                                                                        "option", "p", "rb", "rp", "rt",
                                                                                        "rtc", "tbody", "td", "tfoot",
                                                                                        "th", "thead", "tr"]):
            self._open_elements.pop()

    def _reconstruct_the_active_formatting_elements(self) -> None:
        if self._formatting_elements.isEmpty():
            return

        entry = self._formatting_elements.lastEntry()
        if entry.isMarker or entry.element.name == self._open_elements.contains(entry.element.name):
            return

        def rewind(entry: ListOfActiveElements.Entry) -> Optional[ListOfActiveElements.Entry]:
            return self._formatting_elements.entryBefore(entry)


        if len(self._formatting_elements.entries()) > 1:
            entry = rewind(entry)
            while entry and entry.isMarker is False and self._open_elements.contains(entry.element.name) is False:
                entry = rewind(entry)
            entry = self._formatting_elements.entryAfter(entry)


    def _close_ap_element(self) -> None:
        self._generate_implied_end_tags("p")
        if self._current_element.name != "p":
            # TODO: Handle parse error.
            pass
        self._open_elements.pop_until_element_with_tag_name_has_been_popped("p")

    def _reset_insertion_mode_appropriately(self) -> None:
        last = self._open_elements.last()

        if not last:
            return

        if last.name == "select":
            self._switchModeTo(self._Mode.InSelect)
        elif last.name in ["td", "th"]:
            self._switchModeTo(self._Mode.InCell)
        elif last.name == "tr":
            self._switchModeTo(self._Mode.InRow)
        elif last.name in ["tbody", "thead", "tfoot"]:
            self._switchModeTo(self._Mode.InTableBody)
        elif last.name == "caption":
            self._switchModeTo(self._Mode.InCaption)
        elif last.name == "colgroup":
            self._switchModeTo(self._Mode.InColumnGroup)
        elif last.name == "table":
            self._switchModeTo(self._Mode.InTable)
        elif last.name == "template":
            self._switchModeTo(self._Mode.InTemplate)
        elif last.name == "head":
            self._switchModeTo(self._Mode.InHead)
        elif last.name == "body":
            self._switchModeTo(self._Mode.InBody)
        elif last.name == "frameset":
            self._switchModeTo(self._Mode.InFrameset)
        elif last.name == "html":
            self._switchModeTo(self._Mode.AfterAfterBody)
        else:
            self._switchModeTo(self._Mode.InBody)

    def _find_appropriate_place_for_inserting_node(self) -> AdjustedInsertionLocation:
        target = self._current_element
        adjusted_location = self.AdjustedInsertionLocation()

        if self._foster_parenting and target.name in ["table", "tbody", "tfoot", "thead", "tr"]:
            template_result = self._open_elements.last_element_with_tag_name("template")
            table_result = self._open_elements.last_element_with_tag_name("table")
            if (template_result is not None and table_result is None or (
                    table_result is not None and table_result.index < template_result.index)):
                adjusted_location.parent = template_result.element
                adjusted_location.insert_before_sibling = None
                return adjusted_location
            elif table_result is None:
                adjusted_location.parent = self._open_elements.first()
                adjusted_location.insert_before_sibling = None
                return adjusted_location
            elif table_result is not None and table_result.element.parentNode is not None:
                adjusted_location.parent = table_result.element.parentNode
                adjusted_location.insert_before_sibling = table_result.element
                return adjusted_location

            previous_element = self._open_elements.element_before(table_result.element)
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
            documentNode = DocumentType(token, self._document)
            self._document_node = documentNode
            # TODO: Handle quircks mode.
            self._switchModeTo(self._Mode.BeforeHTML)

    def handle_before_html(self, token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
        if token.type == HTMLToken.TokenType.StartTag:
            token = cast(HTMLTag, token)
            if token.name == "html":
                element = self._create_element(token)
                self._open_elements.push(element)
                self._switchModeTo(self._Mode.BeforeHead)
            else:
                token = HTMLTag(HTMLToken.TokenType.StartTag)
                token.name = "html"
                element = self._create_element(token)
                self._open_elements.push(element)
                self._switchModeTo(self._Mode.BeforeHead)

    def handle_before_head(self, token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
        log("handle_before_head")
        if token.type == HTMLToken.TokenType.Character:
            if token.is_parser_white_space():
                self._continue_in(self._Mode.BeforeHead)
        elif token.type == HTMLToken.TokenType.Comment:
            self._insert_comment(token)
        elif token.type == HTMLToken.TokenType.DOCTYPE:
            self._continue_in(self._Mode.BeforeHead)
        elif token.type == HTMLToken.TokenType.StartTag:
            token = cast(HTMLTag, token)
            if token.name == "head":
                element = self._create_element(token)
                self._open_elements.push(element)
                self._switchModeTo(self._Mode.InHead)
        else:
            token = HTMLTag(HTMLToken.TokenType.StartTag)
            token.name = "head"
            element = self._create_element(token)
            self._open_elements.push(element)
            self._switchModeTo(self._Mode.InHead)

    def handle_in_head(self, token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
        if token.type == HTMLToken.TokenType.Character:
            if token.is_parser_white_space():
                self._insert_character(token)
        elif token.type == HTMLToken.TokenType.Comment:
            token = cast(HTMLCommentOrCharacter, token)
            comment = Comment(token.data, self._current_element, self._document)
            self._current_element.appendChild(comment)
        elif token.type == HTMLToken.TokenType.DOCTYPE:
            pass
        elif token.type == HTMLToken.TokenType.StartTag:
            token = cast(HTMLTag, token)
            if token.name == "html":
                # TODO: Handle using the "in body"
                raise NotImplementedError
            elif token.name in ["base", "basefont", "bgsound", "link"]:
                # This kind of elements are not added to open stack.
                _ = self._create_element(token)
            elif token.name == "meta":
                # This kind of elements are not added to open stack.
                element = self._create_element(token)
                if "charset" in element.attributes:
                    # TODO: Handle charset attribute.
                    pass

            elif token.name == "title":
                element = self._create_element(token)
                self._open_elements.push(element)
                self._tokenizer.switch_state_to(
                    self._tokenizer.State.RCDATA)
                log("Assigning insertion mode:", self._current_insertion_mode)
                self._original_insertion_mode = self._current_insertion_mode
                self._switchModeTo(self._Mode.Text)
            elif (token.name == "noscript" and self._scripting) or (token.name in ["noframes", "style"]):
                element = self._create_element(token)
                self._open_elements.push(element)
                self._tokenizer.switch_state_to(
                    self._tokenizer.State.RAWTEXT)
                self._original_insertion_mode = self._current_insertion_mode
                self._switchModeTo(self._Mode.Text)
            elif token.name == "noscript" and not self._scripting:
                element = self._create_element(token)
                self._open_elements.push(element)
                self._switchModeTo(self._Mode.InHeadNoscript)
            elif token.name == "script":
                # TODO: Add support for JS.
                adjusted_insertion_location = self._find_appropriate_place_for_inserting_node()
                element = cast(HTMLScriptElement,
                               self._create_element_with_adjusted_location(token, adjusted_insertion_location))
                element.parserDocument = self._document
                element.isNonBlocking = False

                if self.parsing_fragment:
                    raise NotImplementedError
                if self.invokef_while_document_write:
                    raise NotImplementedError

                self._open_elements.push(element)
                self._tokenizer.switch_state_to(self._tokenizer.State.ScriptData)
                self._original_insertion_mode = self._current_insertion_mode
                self._switchModeTo(self._Mode.Text)

            elif token.name == "template":
                element = self._create_element(token)
                self._open_elements.push(element)
                self._formatting_elements.addMarker()
                self._frameset_ok = False
                # self._switchModeTo(self._Mode.InTemplate)
                # TODO: Handle rest of the case.
            else:
                # Ignores "head" and any other tag.
                pass

        elif token.type == HTMLToken.TokenType.EndTag:
            if token.name == "head":
                log("removing head")
                log(self._open_elements.elements())
                self._open_elements.pop_until_element_with_tag_name_has_been_popped(token.name)
                self._switchModeTo(self._Mode.AfterHead)
            elif token.name in ["body", "html", "br"]:
                self._open_elements.pop()
                self._reconsumeIn(self._Mode.AfterHead, token)
            elif token.name == "template":
                if not self._open_elements.contains("template"):
                    pass
                else:
                    self._open_elements.pop_until_element_with_tag_name_has_been_popped("template")
                    self._formatting_elements.clearUpToTheLastMarker()
                    self._reset_insertion_mode_appropriately()
                # TODO: Handle rest of the case.
        else:
            self._open_elements.pop()
            self._reconsumeIn(self._Mode.AfterHead, token)

    def handle_in_head_noscript(self, token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
        if token.type == HTMLToken.TokenType.DOCTYPE:
            pass
        elif token.type == HTMLToken.TokenType.EndTag:
            token = cast(HTMLTag, token)
            if token.name == "noscript":
                log("removing noscript")
                log(self._open_elements.elements())
                self._open_elements.pop()
                self._switchModeTo(self._Mode.InHead)
            elif token.name == "br":
                self._open_elements.pop()
            else:
                pass
        elif token.type == HTMLToken.TokenType.Character:
            if token.is_parser_white_space():
                self._insert_character(token)
            else:
                self._insert_character(token)
        elif token.type == HTMLToken.TokenType.Comment:
            token = cast(HTMLCommentOrCharacter, token)
            comment = Comment(token.data, self._current_element, self._document)
            self._current_element.appendChild(comment)
        elif token.type == HTMLToken.TokenType.StartTag:
            if token.name in ["basefont", "bgsound", "link", "noframes", "style"]:
                element = self._create_element(token)
                self._open_elements.push(element)
            elif token.name in ["meta"]:
                pass
            elif token.name in ["head", "noscript"]:
                pass
            elif token.name == "html":
                # TODO: Handle using the "in body".
                raise NotImplementedError
        else:
            self._open_elements.pop()
            self._current_element = self._open_elements.last_element_with_tag_name("head")
            self._switchModeTo(self._Mode.InHead)

    def handle_after_head(self, token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
        log("handle_after_head", token)
        if token.type == HTMLToken.TokenType.Character:
            if token.is_parser_white_space():
                self._insert_character(token)
        elif token.type == HTMLToken.TokenType.Comment:
            self._insert_comment(token)
        elif token.type == HTMLToken.TokenType.DOCTYPE:
            pass  # Ignore token
        elif token.type == HTMLToken.TokenType.StartTag:
            token = cast(HTMLTag, token)
            if token.name == "html":
                # TODO: Handle using the "in body".
                raise NotImplementedError
            elif token.name == "body":
                log("Yes here")
                log(self._open_elements.elements())
                element = self._create_element(token)
                self._open_elements.push(element)
                self._switchModeTo(self._Mode.InBody)
            elif token.name == "frameset":
                raise NotImplementedError  # TODO: Handle case.
            elif (token.name in ["base", "basefont", "bgsound", "link", "meta", "noframes", "script", "style","template", "title"]):
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
                element = self._create_element(_token)
                self._open_elements.push(element)
                self._frameset_ok = False
                self._reconsumeIn(self._Mode.InBody, token)
            else:
                pass  # Ignore token.
        else:
            _token = HTMLTag(HTMLToken.TokenType.StartTag)
            _token.name = "body"
            element = self._create_element(_token)
            self._open_elements.push(element)
            self._reconsumeIn(self._Mode.InBody, token)

    def handle_in_body(self, token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
        if token.type == HTMLToken.TokenType.Character:
            if token.data is None:
                pass  # Ignore token.
            elif token.is_parser_white_space():
                # TODO: Reconstruct the active formatting elements, if any.
                self._insert_character(token)
            else:
                # TODO: Reconstruct the active formatting elements, if any.
                self._insert_character(token)
                self._frameset_ok = False
        elif token.type == HTMLToken.TokenType.Comment:
            self._insert_comment(token)
        elif token.type == HTMLToken.TokenType.DOCTYPE:
            pass  # Ignore token.
        elif token.type == HTMLToken.TokenType.StartTag:
            if token.name == "html":
                raise NotImplementedError  # Handle case
            elif token.name == "template":
                # Handle case, Process the token using the rules for the "in head" insertion mode.
                element = self._create_element(token)
                self._open_elements.push(element)
                self._formatting_elements.addMarker()
                self._frameset_ok = False
                self._switchModeTo(self._Mode.InTemplate)
            elif token.name in ["noframes", "style"]:
                element = self._create_element(token)
                self._open_elements.push(element)
                self._tokenizer.switch_state_to(
                    self._tokenizer.State.RAWTEXT)
                self._original_insertion_mode = self._current_insertion_mode
                self._switchModeTo(self._Mode.Text)
            elif token.name in ["base", "basefont", "bgsound", "link"]:
                # This kind of elements are not added to open stack.
                _ = self._create_element(token)
            elif token.name == "meta":
                # This kind of elements are not added to open stack.
                element = self._create_element(token)
                if "charset" in element.attributes:
                    # TODO: Handle charset attribute.
                    pass
            elif token.name == "title":
                element = self._create_element(token)
                self._open_elements.push(element)
                self._tokenizer.switch_state_to(
                    self._tokenizer.State.RCDATA)
                self._original_insertion_mode = self._current_insertion_mode
                self._switchModeTo(self._Mode.Text)
            elif token.name == "script":
                # TODO: Add support for JS.
                adjustedInsertionLocation = self._find_appropriate_place_for_inserting_node()
                element = cast(HTMLScriptElement,
                               self._create_element_with_adjusted_location(token, adjustedInsertionLocation))
                element.parserDocument = self._document
                element.isNonBlocking = False

                if self.parsing_fragment:
                    raise NotImplementedError
                if self.invokef_while_document_write:
                    raise NotImplementedError

                self._open_elements.push(element)
                self._tokenizer.switch_state_to(self._tokenizer.State.ScriptData)
                self._original_insertion_mode = self._current_insertion_mode
                self._switchModeTo(self._Mode.Text)
            elif token.name == "body":
                # TODO: handle parse error.
                pass
            elif token.name == "frameset":
                raise NotImplementedError  # Handle case
            elif (token.name in ["address", "article", "aside", "blockquote", "center", "details", "dialog", "dir",
                                 "div", "dl", "fieldset", "figcaption", "figure", "footer", "header", "hgroup",
                                 "main", "menu", "nav", "ol", "p", "section", "summary", "ul"]):
                if self._open_elements.has_in_button_scope("p"):
                    self._open_elements.pop()
                element = self._create_element(token)
                self._open_elements.push(element)
            elif token.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                if self._open_elements.has_in_button_scope("p"):
                    self._open_elements.pop()
                elif self._current_element.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                    self._open_elements.pop()
                element = self._create_element(token)
                self._open_elements.push(element)
            elif token.name in ["pre", "listing"]:
                if self._open_elements.has_in_button_scope("p"):
                    self._open_elements.pop()
                element = self._create_element(token)
                self._open_elements.push(element)
                # TODO: Handle new line
                self._frameset_ok = False
            elif token.name == "form":
                if self._form_element is not None and self._open_elements.contains("template") is False:
                    # TODO: Handle parse error.
                    pass
                elif self._open_elements.has_in_button_scope("p"):
                    self._open_elements.pop_until_element_with_tag_name_has_been_popped("p")

                element = self._create_element(token)
                self._open_elements.push(element)

                if self._open_elements.contains("template") is False:
                    self._form_element = element
            elif token.name == "li":
                self._frameset_ok = False

                for element in reversed(self._open_elements.elements()):
                    node = element
                    if self._current_element.name == "li":
                        self._generate_implied_end_tags("li")
                        if self._current_element.name == "li":
                            # TODO: Handle parse error
                            pass
                        self._open_elements.pop_until_element_with_tag_name_has_been_popped("li")
                        break

                    if tag_is_special(node.name) and node.name not in ["address", "div", "p"]:
                        break

                if self._open_elements.has_in_button_scope("p"):
                    self._close_ap_element()

                element = self._create_element(token)
                self._open_elements.push(element)

            elif token.name in ["dd", "dt"]:
                log(token.name)
                self._frameset_ok = False
                element = self._create_element(token)
                self._open_elements.push(element)
                #if token.name == "dd":
                # TODO: Handle the case properly
                #raise NotImplementedError
            elif token.name == "plaintext":
                if self._open_elements.has_in_button_scope("p"):
                    self._open_elements.pop()
                element = self._create_element(token)
                self._open_elements.push(element)
                self._tokenizer.switch_state_to(
                    self._tokenizer.State.PLAINTEXT)
            elif token.name == "button":
                if self._open_elements.has_in_scope(token.name):
                    self._open_elements.pop_until_element_with_tag_name_has_been_popped(token.name)
                # TODO: Reconstruct the active formatting elements, if any.
                self._frameset_ok = False
                element = self._create_element(token)
                self._open_elements.push(element)
            elif token.name == "a":
                if self._open_elements.has_in_scope(token.name):
                    self._open_elements.pop_until_element_with_tag_name_has_been_popped(token.name)

                element = self._create_element(token)
                self._open_elements.push(element)
            elif (token.name in ["b", "big", "code", "em", "font", "i", "s", "small", "strike", "strong", "tt",
                                 "u"]):
                # TODO: Reconstruct the active formatting elements, if any and add handling to all tother places too
                element = self._create_element(token)
                self._open_elements.push(element)
            elif token.name == "nobr":
                if self._open_elements.has_in_scope(token.name):
                    # TODO: run the adoption agency algorithm for the token
                    raise NotImplementedError
                self._create_element(token)
            # TODO: Push onto the list of active formatting elements that element. Add this handling to other places too.
            elif token.name in ["area", "br", "embed", "img", "keygen", "wbr"]:
                # TODO: Construct active elements.
                element = self._create_element(token)
                self._open_elements.push(element)
                self._open_elements.pop()
            elif token.name == "input":
               self._create_element(token)
            elif token.name == "textarea":
                element = self._create_element(token)
                self._open_elements.push(element)
                # TODO: Handle new line
                self._tokenizer.switch_state_to(self._tokenizer.State.RCDATA)
                self._original_insertion_mode = self._current_insertion_mode
                self._frameset_ok = False
                self._switchModeTo(self._Mode.Text)
            else:
                # TODO: Construct active elements.
                element = self._create_element(token)
                self._open_elements.push(element)
        elif token.type == HTMLToken.TokenType.EndTag:
            if token.name == "template":
                # Handle case, Process the token using the rules for the "in head" insertion mode.
                if not self._open_elements.contains("template"):
                    pass
                else:
                    self._open_elements.pop_until_element_with_tag_name_has_been_popped("template")
                    self._formatting_elements.clearUpToTheLastMarker()
                    self._reset_insertion_mode_appropriately()
                # TODO: Handle rest of the case.
            elif token.name == "body":
                log("Closing body element")
                open_body_element = self._open_elements.last_element_with_tag_name(token.name)
                if open_body_element is None:
                    log("No body tag in open stack")
                    pass  # Ignore token.
                # TODO: handle the else case.
                else:
                    self._switchModeTo(self._Mode.AfterBody)
                    self._open_elements.pop_until_element_with_tag_name_has_been_popped(token.name)
                    # TODO: Implement the popping functionality.
                    self._switchModeTo(self._Mode.AfterBody)
            elif token.name == "html":
                self._reconsumeIn(self._Mode.AfterBody, token)
            elif (token.name in ["address", "article", "aside", "blockquote", "button", "center", "details",
                                 "dialog", "dir", "div", "dl", "fieldset", "figcaption", "figure", "footer",
                                 "header", "hgroup", "listing", "main", "menu", "nav", "ol", "pre", "section",
                                 "summary", "ul"]):
                if not self._open_elements.has_in_scope(token.name):
                    pass
                else:
                    # TODO: Generate implied end tags
                    if not self._open_elements.current_node().name == token.name:
                        # TODO: Handle parse error
                        pass

                    self._open_elements.pop_until_element_with_tag_name_has_been_popped(token.name)
            elif token.name == "form":
                if self._open_elements.contains("template") is False:
                    node = self._form_element
                    self._form_element = None
                    if node is None or self._open_elements.has_in_scope(node.name) is False:
                        # TODO: Handle parse error.
                        return
                    self._generate_implied_end_tags()
                    if self._current_element != node:
                        # TODO: Handle parse error
                        pass
                    self._open_elements.pop_until_element_with_tag_name_has_been_popped(node.name)
                else:
                    if self._open_elements.has_in_scope("form"):
                        # TODO: Handle parse error.
                        return
                    self._generate_implied_end_tags()
                    if self._current_element.name != "form":
                        # TODO: Handle parse error
                        pass
                    self._open_elements.pop_until_element_with_tag_name_has_been_popped("form")

            elif token.name == "p":
                if not self._open_elements.has_in_button_scope("p"):
                    element = self._create_element(token)
                    self._open_elements.push(element)
                self._open_elements.pop()
            elif token.name == "li":
                if not self._open_elements.has_in_list_item_scope(token.name):
                    # TODO: Handle parse rror.
                    return

                self._generate_implied_end_tags(token.name)
                if self._current_element.name != "li":
                    # TODO: Handle parse error.
                    pass
                log("Removing 'li'")
                self._open_elements.pop_until_element_with_tag_name_has_been_popped("li")
            elif token.name in ["dd", "dt"]:
                if not self._open_elements.has_in_scope(token.name):
                    raise NotImplementedError  # TODO: handle parse error.

                if self._current_element.name != token.name:
                    raise NotImplementedError  # TODO: handle parse error.

                while not self._open_elements.is_empty():
                    poppedElement = self._open_elements.pop()
                    if poppedElement.name == token.name:
                        break
                return
            elif token.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                if not self._open_elements.has_in_scope(token.name):
                    raise NotImplementedError  # TODO: handle parse error.
                    return

                if self._current_element.name != token.name:
                    raise NotImplementedError  # TODO: handle parse error.

                while not self._open_elements.is_empty():
                    poppedElement = self._open_elements.pop()
                    if poppedElement.name == token.name:
                        break
                return
            elif token.name == "sarcasm":
                # TODO: Handle case
                raise NotImplementedError
            elif (token.name in ["a", "b", "big", "code", "em", "font", "i", "nobr", "s", "small", "strike",
                                 "strong", "tt", "u"]):
                # TODO: Run the adoption agency algorithm for the token.
                self._adoption_agency_algorithm(token)
            else:

                for element in reversed(self._open_elements.elements()):
                    node = element
                    if node.name == token.name:
                        self._generate_implied_end_tags(token.name)
                        if node != self._current_element:
                            # TODO: Handle parse error.
                            pass

                        while self._current_element.name != node.name:
                            self._open_elements.pop()

                        self._open_elements.pop()
                        break

                    if tag_is_special(node.name):
                        # TODO: Handle parse error.
                        return

        elif token.type == HTMLToken.TokenType.EOF:
            for node in self._open_elements.elements():
                if node.name not in ["dd", "dt", "li", "optgroup", "option", "p", "rb", "rp", "rt", "rtc", "tbody",
                                     "td", "tfoot", "th", "thead", "tr", "body", "html"]:
                    # TODO: Handle parse error.
                    raise NotImplementedError()

            # TODO: This is a hack, check if valid
            self._open_elements.pop_until_element_with_tag_name_has_been_popped("body")
            # TODO: Implement the popping functionality.
            self._reconsumeIn(self._Mode.AfterBody, token)

            return

    def handle_text(self, token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
        if token.type == HTMLToken.TokenType.Character:
            self._insert_character(token)
        elif token.type == HTMLToken.TokenType.EOF:
            if self._current_element.name == "script":
                # TODO: Mark the script element as "already started".
                pass
            self._open_elements.pop()
            if self._original_insertion_mode is not None:
                self._reconsumeIn(self._original_insertion_mode, token)
        elif token.type == HTMLToken.TokenType.EndTag and token.name == "script":
            # TODO: flush_character_insertions()
            script = self._current_element
            self._open_elements.pop()
            if self._original_insertion_mode is not None:
                self._switchModeTo(self._original_insertion_mode)
        # TODO: HAndle rest of the case.
        else:
            self._open_elements.pop()
            if self._original_insertion_mode is not None:
                self._switchModeTo(self._original_insertion_mode)

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

    def handle_in_template(self, token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
        if token.type in [HTMLToken.TokenType.Character, HTMLToken.TokenType.Comment, HTMLToken.TokenType.DOCTYPE]:
            self._reconsumeIn(self._Mode.InBody, token)
        elif token.type == HTMLToken.TokenType.StartTag:
            token = cast(HTMLTag, token)
            if token.name in ["base", "basefont", "bgsound", "link", "meta", "noframes", "script", "style", "template",
                              "title"]:
                self._reconsumeIn(self._Mode.InHead, token)
            elif token.name in ["caption", "colgroup", "tbody", "tfoot", "thead"]:
                self._open_elements.pop()
                self._open_elements.push(cast(Element, self._current_element.parentNode))
                self._reconsumeIn(self._Mode.InTable, token)
            elif token.name == "col":
                self._open_elements.pop()
                self._reconsumeIn(self._Mode.InColumnGroup, token)
            elif token.name == "tr":
                self._open_elements.pop()
                self._open_elements.push(cast(Element, self._current_element.parentNode))
                self._reconsumeIn(self._Mode.InTableBody, token)
            elif token.name in ["td", "th"]:
                self._open_elements.pop()
                self._open_elements.push(cast(Element, self._current_element.parentNode))
                self._reconsumeIn(self._Mode.InRow, token)
            else:
                self._reconsumeIn(self._Mode.InBody, token)
        elif token.type == HTMLToken.TokenType.EndTag:
            if token.name == "template":
                if self._open_elements.contains("template") is False:
                    pass
            else:
                self._reconsumeIn(self._Mode.InBody, token)

    def handle_after_body(self, token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]) -> None:
        if token.type == HTMLToken.TokenType.EOF:
            self._open_elements.pop_all_elements()
        return

    def handle_in_frameset(self) -> None:
        return

    def handle_after_frameset(self) -> None:
        return

    def handle_after_after_body(self) -> None:
        return

    def handle_after_after_frameset(self) -> None:
        return

    def _get_mode_switcher(self) -> Optional[Any]:  # TODO: Check typing

        switcher = {
            self._Mode.Initial: self.handle_initial,
            self._Mode.BeforeHTML: self.handle_before_html,
            self._Mode.BeforeHead: self.handle_before_head,
            self._Mode.InHead: self.handle_in_head,
            self._Mode.InHeadNoscript: self.handle_in_head_noscript,
            self._Mode.AfterHead: self.handle_after_head,
            self._Mode.InBody: self.handle_in_body,
            self._Mode.Text: self.handle_text,
            self._Mode.InTable: self.handle_in_table,
            self._Mode.InTableText: self.handle_in_table_text,
            self._Mode.InCaption: self.handle_in_caption,
            self._Mode.InColumnGroup: self.handle_in_column_group,
            self._Mode.InTableBody: self.handle_in_table_body,
            self._Mode.InRow: self.handle_in_row,
            self._Mode.InCell: self.handle_in_cell,
            self._Mode.InSelect: self.handle_in_select,
            self._Mode.InSelectInTable: self.handle_in_select_in_table,
            self._Mode.InTemplate: self.handle_in_template,
            self._Mode.AfterBody: self.handle_after_body,
            self._Mode.InFrameset: self.handle_in_frameset,
            self._Mode.AfterFrameset: self.handle_after_frameset,
            self._Mode.AfterAfterBody: self.handle_after_after_body,
            self._Mode.AfterAfterFrameset: self.handle_after_after_frameset,
        }

        return switcher.get(self._current_insertion_mode)

    def current_insertion_mode(self) -> _Mode:
        return self._current_insertion_mode
