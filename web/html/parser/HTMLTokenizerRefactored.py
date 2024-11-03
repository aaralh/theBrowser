from dataclasses import dataclass
from enum import Enum, auto
from typing import Union, Callable, Any, cast, List, Optional
from .HTMLToken import HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter
from .utils import char_is_alpha, char_is_control, char_is_noncharacter, char_is_whitespace, char_is_uppercase_alpha, \
    char_is_lowercase_alpha, char_is_surrogate
from .Entities import getNamedCharFromTable, atLeastOneNameStartsWith
import string
from browser.utils.logging import log

DEBUG = False

@dataclass
class Emit:
    token: HTMLTag

@dataclass
class SwitchTo:
    pass

@dataclass
class ReConsume:
    input_character: str

@dataclass
class ReprocessQueue:
    pass

TokenizerState = Union[Emit, SwitchTo, ReConsume, ReprocessQueue]

class HTMLTokenizer:

    def __init__(self, html = ""):
        self.state = self.State.Data
        self._html = html
        self._cursor = 0
        self._current_input_char: str = ""  # TODO: Basically initially is None, fix
        self._return_state: Union[Any, None] = None
        self._current_token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter, None] = None
        self._temporary_buffer: List[str] = []
        self._character_reference_code: int = 0
        self._last_emitted_start_tag_name: Optional[str] = None
        self.queued_tokens: List[HTMLToken] = []

    def _emit_current_token(self) -> Optional[Emit]:
        if self._current_token is not None:
            self._current_token = cast(HTMLTag, self._current_token)
            if self._current_token.type == HTMLToken.TokenType.StartTag:
                self._last_emitted_start_tag_name = self._current_token.name
            if DEBUG:
                log("Current state: ", self.state)
            token = self._current_token
            self._current_token = None
            return Emit(token)

    def _append_token_to_queue(self):
        if self._current_token:
            self.queued_tokens.append(self._current_token)
        self._current_token = None

    @staticmethod
    def _create_new_token(
            token_type: HTMLToken.TokenType
    ) -> Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]:
        token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]
        if token_type == HTMLToken.TokenType.DOCTYPE:
            token = HTMLDoctype()
        elif token_type == HTMLToken.TokenType.Comment or token_type == HTMLToken.TokenType.Character:
            token = HTMLCommentOrCharacter(token_type)
        elif token_type == HTMLToken.TokenType.StartTag or token_type == HTMLToken.TokenType.EndTag:
            token = HTMLTag(token_type)
        else:
            token = HTMLToken(token_type)
        return token

    class State(Enum):
        Data = auto()
        RCDATA = auto()
        RAWTEXT = auto()
        ScriptData = auto()
        PLAINTEXT = auto()
        TagOpen = auto()
        EndTagOpen = auto()
        TagName = auto()
        RCDATALessThanSign = auto()
        RCDATAEndTagOpen = auto()
        RCDATAEndTagName = auto()
        RAWTEXTLessThanSign = auto()
        RAWTEXTEndTagOpen = auto()
        RAWTEXTEndTagName = auto()
        ScriptDataLessThanSign = auto()
        ScriptDataEndTagOpen = auto()
        ScriptDataEndTagName = auto()
        ScriptDataEscapeStart = auto()
        ScriptDataEscapeStartDash = auto()
        ScriptDataEscaped = auto()
        ScriptDataEscapedDash = auto()
        ScriptDataEscapedDashDash = auto()
        ScriptDataEscapedLessThanSign = auto()
        ScriptDataEscapedEndTagOpen = auto()
        ScriptDataEscapedEndTagName = auto()
        ScriptDataDoubleEscapeStart = auto()
        ScriptDataDoubleEscaped = auto()
        ScriptDataDoubleEscapedDash = auto()
        ScriptDataDoubleEscapedDashDash = auto()
        ScriptDataDoubleEscapedLessThanSign = auto()
        ScriptDataDoubleEscapeEnd = auto()
        BeforeAttributeName = auto()
        AttributeName = auto()
        AfterAttributeName = auto()
        BeforeAttributeValue = auto()
        AttributeValueDoubleQuoted = auto()
        AttributeValueSingleQuoted = auto()
        AttributeValueUnquoted = auto()
        AfterAttributeValueQuoted = auto()
        SelfClosingStartTag = auto()
        BogusComment = auto()
        MarkupDeclarationOpen = auto()
        CommentStart = auto()
        CommentStartDash = auto()
        Comment = auto()
        CommentLessThanSign = auto()
        CommentLessThanSignBang = auto()
        CommentLessThanSignBangDash = auto()
        CommentLessThanSignBangDashDash = auto()
        CommentEndDash = auto()
        CommentEnd = auto()
        CommentEndBang = auto()
        DOCTYPE = auto()
        BeforeDOCTYPEName = auto()
        DOCTYPEName = auto()
        AfterDOCTYPEName = auto()
        AfterDOCTYPEPublicKeyword = auto()
        BeforeDOCTYPEPublicIdentifier = auto()
        DOCTYPEPublicIdentifierDoubleQuoted = auto()
        DOCTYPEPublicIdentifierSingleQuoted = auto()
        AfterDOCTYPEPublicIdentifier = auto()
        BetweenDOCTYPEPublicAndSystemIdentifiers = auto()
        AfterDOCTYPESystemKeyword = auto()
        BeforeDOCTYPESystemIdentifier = auto()
        DOCTYPESystemIdentifierDoubleQuoted = auto()
        DOCTYPESystemIdentifierSingleQuoted = auto()
        AfterDOCTYPESystemIdentifier = auto()
        BogusDOCTYPE = auto()
        CDATASection = auto()
        CDATASectionBracket = auto()
        CDATASectionEnd = auto()
        CharacterReference = auto()
        NamedCharacterReference = auto()
        AmbiguousAmpersand = auto()
        NumericCharacterReference = auto()
        HexadecimalCharacterReferenceStart = auto()
        DecimalCharacterReferenceStart = auto()
        HexadecimalCharacterReference = auto()
        DecimalCharacterReference = auto()
        NumericCharacterReferenceEnd = auto()

    def _continue_in(self, state: State) -> SwitchTo:
        return self.switch_state_to(state)

    def _ignore_character_and_continue_to(self, new_state: State) -> SwitchTo:
        return self.switch_state_to(new_state)

    def switch_state_to(self, new_state: State) -> SwitchTo:
        """
        Switch state and consume next character.
        """
        self.state = new_state
        return SwitchTo()

    def _reconsume_in(self, new_state: State) -> ReConsume:
        """
        Switch state without consuming next character.
        """
        self.state = new_state
        return ReConsume(self._current_input_char)

    def _reconsume_in_return_state(self) -> ReprocessQueue:
        self.state = self._return_state
        return ReprocessQueue()


    def _next_characters_are(self, characters: str) -> bool:
        """
        Check if given characters follow the current _cursor position in _html.
        """
        for index in range(len(characters)):
            if self._cursor >= len(self._html):
                return False
            char = self._html[self._cursor + index]
            if char.lower() != characters[index].lower():
                return False

        return True

    def _consume_characters(self, characters: str) -> None:
        self._cursor += len(characters)

    def _next_code_point(self) -> Union[str, None]:
        if self._cursor >= len(self._html):
            return None
        char = self._html[self._cursor]
        self._cursor += 1
        return char

    def _flush_temporary_buffer(self) -> None:
        if self._current_token is not None:
            self._current_token = cast(HTMLTag, self._current_token)
            self._current_token.add_char_to_attribute_value("".join(self._temporary_buffer))
        else:
            for char in self._temporary_buffer:
                self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
                self._current_token.data = char
                self._append_token_to_queue()
        self._temporary_buffer = []

    # 13.2.5.1 https://html.spec.whatwg.org/multipage/parsing.html#data-state
    def handle_data(self) -> TokenizerState:
        if self._current_input_char == "&":
            self._return_state = self.State.Data
            return self.switch_state_to(self.State.CharacterReference)
        elif self._current_input_char == "<":
            return self.switch_state_to(self.State.TagOpen)
        elif self._current_input_char is None:
            self._current_token = self._create_new_token(HTMLToken.TokenType.EOF)
            return self._emit_current_token()
        elif ord(self._current_input_char) == 0:
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = "\uFFFD"
            return self._emit_current_token()
        else:
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = self._current_input_char
            return self._emit_current_token()

    def handle_RCDATA(self) -> None:
        if self._current_input_char == "&":
            self._return_state = self.State.RCDATA
            self.switch_state_to(self.State.CharacterReference)
        elif self._current_input_char == "<":
            self.switch_state_to(self.State.RCDATALessThanSign)
        elif self._current_input_char is None:
            self._current_token = self._create_new_token(HTMLToken.TokenType.EOF)
            return self._emit_current_token()
        else:
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = self._current_input_char
            return self._emit_current_token()

    def handle_RAWTEXT(self) -> None:
        if self._current_input_char == "<":
            self.switch_state_to(self.State.RAWTEXTLessThanSign)
        elif self._current_input_char is None:
            self._current_token = self._create_new_token(HTMLToken.TokenType.EOF)
            return self._emit_current_token()
        else:
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = self._current_input_char
            return self._emit_current_token()

    def handle_script_data(self) -> None:
        if self._current_input_char == "<":
            self.switch_state_to(self.State.ScriptDataLessThanSign)
        elif self._current_input_char is None:
            self._current_token = self._create_new_token(HTMLToken.TokenType.EOF)
            return self._emit_current_token()
        else:
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = self._current_input_char
            return self._emit_current_token()

    def handle_PLAINTEXT(self) -> None:
        raise NotImplementedError

    # 13.2.5.6 https://html.spec.whatwg.org/multipage/parsing.html#tag-open-state
    def handle_tag_open(self) -> TokenizerState:

        if self._current_input_char is None:
            self._current_token = self._create_new_token(HTMLToken.TokenType.EOF)
            self._append_token_to_queue()
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = "<"
            return self._emit_current_token()

        if self._current_input_char == "!":
            self._reconsume_in(self.State.MarkupDeclarationOpen)
        elif self._current_input_char == "/":
            return self.switch_state_to(self.State.EndTagOpen)
        elif self._current_input_char.isalpha():
            self._current_token = cast(HTMLTag, self._create_new_token(HTMLToken.TokenType.StartTag))
            return self._reconsume_in(self.State.TagName)
        else:
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = "<"
            self._append_token_to_queue()
            return self._reconsume_in(self.State.Data)

    def handle_end_tag_open(self) -> TokenizerState:
        self._current_token = self._create_new_token(HTMLToken.TokenType.EndTag)
        return self._reconsume_in(self.State.TagName)

    def handle_tag_name(self) -> TokenizerState:
        if self._current_input_char is None:
            self._current_token = self._create_new_token(HTMLToken.TokenType.EOF)
            return self._emit_current_token()
        elif char_is_whitespace(self._current_input_char):
            return self.switch_state_to(self.State.BeforeAttributeName)
        elif self._current_input_char == "/":
            return self.switch_state_to(self.State.SelfClosingStartTag)
        elif self._current_input_char == ">":
            self.switch_state_to(self.State.Data)
            return self._emit_current_token()
        else:
            self._current_token = cast(HTMLTag, self._current_token)
            if self._current_token.name is not None and self._current_input_char is not None:
                self._current_token.name += self._current_input_char
            else:
                self._current_token.name = self._current_input_char
            return self._continue_in(self.State.TagName)

    def handle_RCDATA_less_than_sign(self) -> TokenizerState:
        if self._current_input_char == "/":
            self._temporary_buffer = []
            self.switch_state_to(self.State.RCDATAEndTagOpen)
        else:
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = "<"
            self._append_token_to_queue()
            return self._reconsume_in(self.State.RCDATA)

    def handle_RCDATA_end_tag_open(self) -> TokenizerState:
        if char_is_alpha(self._current_input_char):
            self._current_token = self._create_new_token(HTMLToken.TokenType.EndTag)
            self._current_token = cast(HTMLTag, self._current_token)
            self._current_token.name = ""
            return self._reconsume_in(self.State.RCDATAEndTagName)
        else:
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = "<"
            self._append_token_to_queue()
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = "/"
            self._append_token_to_queue()
            return self._reconsume_in(self.State.RCDATA)

    def handle_RCDATA_end_tag_name(self) -> TokenizerState:
        self._current_token = cast(HTMLTag, self._current_token)

        def else_case() -> TokenizerState:
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = "<"
            self._append_token_to_queue()
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = "/"
            self._append_token_to_queue()

            for char in self._temporary_buffer:
                self._current_token = cast(HTMLCommentOrCharacter,
                                            self._create_new_token(HTMLToken.TokenType.Character))
                self._current_token.data = char
                self._append_token_to_queue()
            return self._reconsume_in(self.State.RCDATA)

        if char_is_whitespace(self._current_input_char):
            if self._current_token.name == self._last_emitted_start_tag_name:
                self.switch_state_to(self.State.BeforeAttributeName)
            else:
                return else_case()
        elif self._current_input_char == "/":
            if self._current_token.name == self._last_emitted_start_tag_name:
                self.switch_state_to(self.State.SelfClosingStartTag)
            else:
                return else_case()
        elif self._current_input_char == ">":
            if self._current_token.name == self._last_emitted_start_tag_name:
                self.switch_state_to(self.State.Data)
                return self._emit_current_token()
            else:
                return else_case()
        elif char_is_uppercase_alpha(self._current_input_char):
            self._current_token.append_char_to_token_name(self._current_input_char.lower())
            self._temporary_buffer.append(self._current_input_char)
        elif char_is_lowercase_alpha(self._current_input_char):
            self._current_token.append_char_to_token_name(self._current_input_char)
            self._temporary_buffer.append(self._current_input_char)
        else:
            return else_case()

    def handle_RAWTEXT_less_than_sign(self) -> TokenizerState:
        if self._current_input_char == "/":
            self._temporary_buffer = []
            self.switch_state_to(self.State.RAWTEXTEndTagOpen)
        else:
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = "<"
            self._append_token_to_queue()
            return self._reconsume_in(self.State.RAWTEXT)

    def handle_RAWTEXT_end_tag_open(self) -> TokenizerState:
        if char_is_alpha(self._current_input_char):
            self._current_token = self._create_new_token(HTMLToken.TokenType.EndTag)
            self._current_token = cast(HTMLTag, self._current_token)
            self._current_token.name = ""
            return self._reconsume_in(self.State.RAWTEXTEndTagName)
        else:
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = "<"
            self._append_token_to_queue()
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = "/"
            self._append_token_to_queue()
            return self._reconsume_in(self.State.RAWTEXT)

    def handle_RAWTEXT_end_tag_name(self) -> TokenizerState:
        self._current_token = cast(HTMLTag, self._current_token)

        def else_case() -> TokenizerState:
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = "<"
            self._append_token_to_queue()
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = "/"
            self._append_token_to_queue()

            for char in self._temporary_buffer:
                self._current_token = cast(HTMLCommentOrCharacter,
                                            self._create_new_token(HTMLToken.TokenType.Character))
                self._current_token.data = char
                self._append_token_to_queue()
            return self._reconsume_in(self.State.RAWTEXT)

        if char_is_whitespace(self._current_input_char):
            if self._current_token.name == self._last_emitted_start_tag_name:
                self.switch_state_to(self.State.BeforeAttributeName)
            else:
                return else_case()
        elif self._current_input_char == "/":
            if self._current_token.name == self._last_emitted_start_tag_name:
                self.switch_state_to(self.State.SelfClosingStartTag)
            else:
                return else_case()
        elif self._current_input_char == ">":
            if self._current_token.name == self._last_emitted_start_tag_name:
                self.switch_state_to(self.State.Data)
                return self._emit_current_token()
            else:
                return else_case()
        elif char_is_uppercase_alpha(self._current_input_char):
            self._current_token.append_char_to_token_name(self._current_input_char.lower())
            self._temporary_buffer.append(self._current_input_char)
        elif char_is_lowercase_alpha(self._current_input_char):
            self._current_token.append_char_to_token_name(self._current_input_char)
            self._temporary_buffer.append(self._current_input_char)
        else:
            return else_case()

    def handle_script_data_less_than_sign(self) -> TokenizerState:
        if self._current_input_char == "/":
            self._temporary_buffer = []
            return self.switch_state_to(self.State.ScriptDataEndTagOpen)
        elif self._current_input_char == "!":
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = "<"
            self._append_token_to_queue()
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = "!"
            self._append_token_to_queue()
            return self.switch_state_to(self.State.ScriptDataEscapeStart)
        else:
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = "<"
            self._append_token_to_queue()
            return self._reconsume_in(self.State.ScriptData)

    def handle_script_data_end_tag_open(self) -> TokenizerState:
        if char_is_uppercase_alpha(self._current_input_char) or char_is_lowercase_alpha(self._current_input_char):
            self._current_token = cast(HTMLTag, self._create_new_token(HTMLToken.TokenType.EndTag))
            self._current_token.name = ""
            return self._reconsume_in(self.State.ScriptDataEndTagName)
        else:
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = "<"
            self._append_token_to_queue()
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = "/"
            self._append_token_to_queue()
            return self._reconsume_in(self.State.ScriptData)

    def handle_script_data_end_tag_name(self) -> TokenizerState:
        self._current_token = cast(HTMLTag, self._current_token)

        def else_case() -> TokenizerState:
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = "<"
            self._append_token_to_queue()
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = "/"
            self._append_token_to_queue()
            for char in self._temporary_buffer:
                self._current_token = cast(HTMLCommentOrCharacter,
                                            self._create_new_token(HTMLToken.TokenType.Character))
                self._current_token.data = char
                self._append_token_to_queue()
            return self._reconsume_in(self.State.ScriptData)

        if char_is_whitespace(self._current_input_char):
            if self._current_token.name == self._last_emitted_start_tag_name:
                return self.switch_state_to(self.State.BeforeAttributeName)
            else:
                return else_case()
        elif self._current_input_char == "/":
            if self._current_token.name == self._last_emitted_start_tag_name:
                return self.switch_state_to(self.State.SelfClosingStartTag)
            else:
                return else_case()
        elif self._current_input_char == ">":
            if self._current_token.name == self._last_emitted_start_tag_name:
                self._append_token_to_queue()
                return self.switch_state_to(self.State.Data)
            else:
                return else_case()
        elif char_is_uppercase_alpha(self._current_input_char):
            self._current_token.append_char_to_token_name(self._current_input_char.lower())
            self._temporary_buffer.append(self._current_input_char)
        elif char_is_lowercase_alpha(self._current_input_char):
            self._current_token.append_char_to_token_name(self._current_input_char)
            self._temporary_buffer.append(self._current_input_char)
        else:
            return else_case()

    def handle_script_data_escape_start(self) -> TokenizerState:
        if self._current_input_char == "-":
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = self._current_input_char
            self._append_token_to_queue()
            return self.switch_state_to(self.State.ScriptDataEscapedDash)
        else:
            return self._reconsume_in(self.State.ScriptData)

    def handle_script_data_escape_start_dash(self) -> TokenizerState:
        if self._current_input_char == "-":
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = self._current_input_char
            self._append_token_to_queue()
            return self.switch_state_to(self.State.ScriptDataEscapedDashDash)
        else:
            return self._reconsume_in(self.State.ScriptData)

    def handle_script_data_escaped(self) -> TokenizerState:
        if self._current_input_char == "-":
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = self._current_input_char
            self._append_token_to_queue()
            return self.switch_state_to(self.State.ScriptDataEscapedDashDash)
        elif self._current_input_char == "<":
            return self.switch_state_to(self.State.ScriptDataEscapedLessThanSign)
        elif self._current_input_char is None:
            self._current_token = self._create_new_token(HTMLToken.TokenType.EOF)
            return self._emit_current_token()
        else:
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = self._current_input_char
            return self._emit_current_token()

    def handle_script_data_escaped_dash(self) -> TokenizerState:
        if self._current_input_char == "-":
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = self._current_input_char
            self._append_token_to_queue()
            return self.switch_state_to(self.State.ScriptDataEscapedDashDash)
        elif self._current_input_char == "<":
            return self.switch_state_to(self.State.ScriptDataEscapedLessThanSign)
        elif self._current_input_char is None:
            self._current_token = self._create_new_token(HTMLToken.TokenType.EOF)
            return self._emit_current_token()
        else:
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = self._current_input_char
            self._append_token_to_queue()
            return self.switch_state_to(self.State.ScriptDataEscaped)

    def handle_script_data_escaped_dash_dash(self) -> TokenizerState:
        if self._current_input_char == "-":
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = self._current_input_char
            return self._emit_current_token()
        elif self._current_input_char == "<":
            return self.switch_state_to(self.State.ScriptDataEscapedLessThanSign)
        elif self._current_input_char == ">":
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = self._current_input_char
            self._append_token_to_queue()
            return self.switch_state_to(self.State.ScriptData)
        elif self._current_input_char is None:
            self._current_token = self._create_new_token(HTMLToken.TokenType.EOF)
            return self._emit_current_token()
        else:
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = self._current_input_char
            self._append_token_to_queue()
            return self.switch_state_to(self.State.ScriptDataEscaped)

    def handle_script_data_escaped_less_than_sign(self) -> TokenizerState:
        if self._current_input_char == "/":
            self._temporary_buffer = []
            return self.switch_state_to(self.State.ScriptDataEscapedEndTagOpen)
        elif char_is_alpha(self._current_input_char):
            self._temporary_buffer = []
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = "<"
            self._append_token_to_queue()
            return self._reconsume_in(self.State.ScriptDataDoubleEscapeStart)
        else:
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = "<"
            self._append_token_to_queue()
            return self._reconsume_in(self.State.ScriptDataEscaped)

    def handle_script_data_escaped_end_tag_open(self) -> TokenizerState:
        if char_is_alpha(self._current_input_char):
            log("handle_script_data_escaped_end_tag_open")
            self._current_token = cast(HTMLTag, self._create_new_token(HTMLToken.TokenType.EndTag))
            self._current_token.name = ""
            return self._reconsume_in(self.State.ScriptDataEscapedEndTagName)
        else:
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = "<"
            self._append_token_to_queue()
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = "/"
            self._append_token_to_queue()
            return self._reconsume_in(self.State.ScriptDataEscaped)

    def handle_script_data_escaped_end_tag_name(self) -> TokenizerState:
        log("handle_script_data_escaped_end_tag_name", self._current_input_char)
        self._current_token = cast(HTMLTag, self._current_token)

        def else_case() -> TokenizerState:
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = "<"
            self._append_token_to_queue()
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = "/"
            self._append_token_to_queue()
            for char in self._temporary_buffer:
                self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
                self._current_token.data = char
                self._append_token_to_queue()

            return self._reconsume_in(self.State.ScriptDataEscaped)


        if char_is_whitespace(self._current_input_char):
            if self._last_emitted_start_tag_name == self._current_token.name:
                return self.switch_state_to(self.State.BeforeAttributeName)
            else:
                return else_case()
        elif self._current_input_char == "/":
            if self._last_emitted_start_tag_name == self._current_token.name:
                return self.switch_state_to(self.State.SelfClosingStartTag)
            else:
                return else_case()
        elif self._current_input_char == ">":
            if self._last_emitted_start_tag_name == self._current_token.name:
                self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
                self._current_token.data = self._current_input_char
                self._append_token_to_queue()
                return self.switch_state_to(self.State.Data)
            else:
                return else_case()
        elif char_is_uppercase_alpha(self._current_input_char):
            self._current_token.append_char_to_token_name(self._current_input_char.lower())
            self._temporary_buffer.append(self._current_input_char)
        elif char_is_lowercase_alpha(self._current_input_char):
            self._current_token.append_char_to_token_name(self._current_input_char)
            self._temporary_buffer.append(self._current_input_char)
        else:
            return else_case()

    def handle_script_data_double_escape_start(self) -> TokenizerState:
        if char_is_whitespace(self._current_input_char) or self._current_input_char in ["/", ">"]:
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = self._current_input_char
            self._append_token_to_queue()
            if "".join(self._temporary_buffer) == "script":
                return self.switch_state_to(self.State.ScriptDataDoubleEscaped)
            else:
                return self.switch_state_to(self.State.ScriptDataEscaped)
        elif char_is_uppercase_alpha(self._current_input_char):
            self._temporary_buffer.append(self._current_input_char)
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = self._current_input_char
            return self._emit_current_token()
        elif char_is_lowercase_alpha(self._current_input_char):
            self._temporary_buffer.append(self._current_input_char)
            self._current_token = cast(HTMLCommentOrCharacter, self._create_new_token(HTMLToken.TokenType.Character))
            self._current_token.data = self._current_input_char
            return self._emit_current_token()
        else:
            return self._reconsume_in(self.State.ScriptDataEscaped)



    def handle_script_data_double_escaped(self) -> None:
        raise NotImplementedError

    def handle_script_data_double_escaped_dash(self) -> None:
        raise NotImplementedError

    def handle_script_data_double_escaped_dash_dash(self) -> None:
        raise NotImplementedError

    def handle_script_data_double_escaped_less_than_sign(self) -> None:
        raise NotImplementedError

    def handle_script_data_double_escape_end(self) -> None:
        raise NotImplementedError

    def handle_before_attribute_name(self) -> TokenizerState:
        self._current_token = cast(HTMLTag, self._current_token)

        if self._current_input_char is None:
            return self._reconsume_in(self.State.AfterAttributeName)
        elif char_is_whitespace(self._current_input_char):
            return self._continue_in(self.State.BeforeAttributeName)
        else:
            self._current_token.create_new_attribute()
            return self._reconsume_in(self.State.AttributeName)

    def handle_attribute_name(self) -> TokenizerState:
        self._current_token = cast(HTMLTag, self._current_token)

        if (
                self._current_input_char is None
                or char_is_whitespace(self._current_input_char)
                or self._current_input_char == "/"
                or self._current_input_char == ">"
        ):
            return self._reconsume_in(self.State.AfterAttributeName)
        elif self._current_input_char == "=":
            return self.switch_state_to(self.State.BeforeAttributeValue)
        elif self._current_input_char.isupper() and self._current_input_char.isalpha():
            self._current_token.add_char_to_attribute_name(self._current_input_char.lower())
        else:
            self._current_token.add_char_to_attribute_name(self._current_input_char)
            return self._continue_in(self.State.AttributeName)

    def handle_after_attribute_name(self) -> TokenizerState:
        self._current_token = cast(HTMLTag, self._current_token)

        if char_is_whitespace(self._current_input_char):
            pass
        elif self._current_input_char == "/":
            return self.switch_state_to(self.State.SelfClosingStartTag)
        elif self._current_input_char == "=":
            return self.switch_state_to(self.State.BeforeAttributeValue)
        elif self._current_input_char == ">":
            self.switch_state_to(self.State.Data)
            return self._emit_current_token()
        elif self._current_input_char is None:
            raise NotImplementedError
        else:
            self._current_token.create_new_attribute()
            return self._reconsume_in(self.State.AttributeName)

    def handle_before_attribute_value(self) -> TokenizerState:
        if char_is_whitespace(self._current_input_char):
            return self._continue_in(self.State.BeforeAttributeValue)
        elif self._current_input_char == '"':
            return self.switch_state_to(self.State.AttributeValueDoubleQuoted)
        elif self._current_input_char == "'":
            return self.switch_state_to(self.State.AttributeValueSingleQuoted)
        elif self._current_input_char == ">":
            self._append_token_to_queue()
            return self.switch_state_to(self.State.Data)
        else:
            return self._reconsume_in(self.State.AttributeValueUnquoted)

    def handle_attribute_value_double_quoted(self) -> TokenizerState:
        self._current_token = cast(HTMLTag, self._current_token)
        if self._current_input_char is None:
            self._current_token = self._create_new_token(HTMLToken.TokenType.EOF)
            return self._emit_current_token()
        elif self._current_input_char == '"':
            return self.switch_state_to(self.State.AfterAttributeValueQuoted)
        elif self._current_input_char == "&":
            self._return_state = self.State.AttributeValueDoubleQuoted
            return self.switch_state_to(self.State.CharacterReference)
        else:
            self._current_token.add_char_to_attribute_value(self._current_input_char)
            return self._continue_in(self.State.AttributeValueDoubleQuoted)

    def handle_attribute_value_single_quoted(self) -> TokenizerState:
        self._current_token = cast(HTMLTag, self._current_token)
        if self._current_input_char is None:
            self._current_token = self._create_new_token(HTMLToken.TokenType.EOF)
            return self._emit_current_token()
        elif self._current_input_char == "'":
            return self.switch_state_to(self.State.AfterAttributeValueQuoted)
        elif self._current_input_char == "&":
            self._return_state = self.State.AttributeValueSingleQuoted
            return self.switch_state_to(self.State.CharacterReference)
        else:
            self._current_token.add_char_to_attribute_value(self._current_input_char)
            return self._continue_in(self.State.AttributeValueSingleQuoted)

    def handle_attribute_value_unquoted(self) -> TokenizerState:
        self._current_token = cast(HTMLTag, self._current_token)
        if self._current_input_char is None:
            self._current_token = self._create_new_token(HTMLToken.TokenType.EOF)
            return self._emit_current_token()
        elif char_is_whitespace(self._current_input_char):
            return self.switch_state_to(self.State.BeforeAttributeName)
        elif self._current_input_char == "&":
            self._return_state = self.State.AttributeValueUnquoted
            return self.switch_state_to(self.State.CharacterReference)
        elif self._current_input_char == ">":
            self.switch_state_to(self.State.Data)
            return self._emit_current_token()
        else:
            self._current_token.add_char_to_attribute_value(self._current_input_char)
            return self._continue_in(self.State.AttributeValueUnquoted)

    def handle_after_attribute_value_quoted(self) -> TokenizerState:
        if self._current_input_char is None:
            self._current_token = self._create_new_token(HTMLToken.TokenType.EOF)
            return self._emit_current_token()
        elif char_is_whitespace(self._current_input_char):
            return self.switch_state_to(self.State.BeforeAttributeName)
        elif self._current_input_char == "/":
            return self.switch_state_to(self.State.SelfClosingStartTag)
        elif self._current_input_char == ">":
            self.switch_state_to(self.State.Data)
            return self._emit_current_token()
        else:
            return self._reconsume_in(self.State.BeforeAttributeName)

    def handle_self_closing_start_tag(self) -> TokenizerState:
        self._current_token = cast(HTMLTag, self._current_token)
        if self._current_input_char == ">":
            self._current_token.selfClosing = True
            self._append_token_to_queue()
            return self.switch_state_to(self.State.Data)
        elif self._current_input_char is None:
            self._current_token = self._create_new_token(HTMLToken.TokenType.EOF)
            return self._emit_current_token()
        else:
            return self._reconsume_in(self.State.BeforeAttributeName)

    def handle_bogus_comment(self) -> None:
        raise NotImplementedError

    def handle_markup_declaration_open(self) -> TokenizerState:
        if self._next_characters_are("--"):
            self._consume_characters("--")
            self._current_token = self._create_new_token(HTMLToken.TokenType.Comment)
            return self.switch_state_to(self.State.CommentStart)
        elif self._next_characters_are("DOCTYPE"):
            self._consume_characters("DOCTYPE")
            return self.switch_state_to(self.State.DOCTYPE)

    def handle_comment_start(self) -> TokenizerState:

        if self._current_input_char == "-":
            return self.switch_state_to(self.State.CommentStartDash)
        elif self._current_input_char == ">":
            self._append_token_to_queue()
            return self.switch_state_to(self.State.Data)
        else:
            return self._reconsume_in(self.State.Comment)

    def handle_comment_start_dash(self) -> TokenizerState:
        self._current_token = cast(HTMLCommentOrCharacter, self._current_token)
        if self._current_input_char == "-":
            return self.switch_state_to(self.State.CommentEnd)
        elif self._current_input_char == ">":
            self.switch_state_to(self.State.Data)
            return self._emit_current_token()
        elif self._current_input_char is None:
            self._append_token_to_queue()
            self._current_token = self._create_new_token(HTMLToken.TokenType.EOF)
            return self._emit_current_token()
        else:
            if self._current_token.data is not None:
                self._current_token.data += "-"
            else:
                self._current_token.data = "-"
            return self._reconsume_in(self.State.Comment)

    def handle_comment(self) -> TokenizerState:
        self._current_token = cast(HTMLCommentOrCharacter, self._current_token)
        if self._current_input_char == "<":
            if self._current_token.data is not None:
                self._current_token.data += self._current_input_char
            else:
                self._current_token.data = self._current_input_char
            return self.switch_state_to(self.State.CommentLessThanSign)
        elif self._current_input_char == "-":
            return self.switch_state_to(self.State.CommentEndDash)
        elif self._current_input_char is None:
            self._append_token_to_queue()
            self._current_token = self._create_new_token(HTMLToken.TokenType.EOF)
            return self._emit_current_token()
        else:
            if self._current_token.data is not None:
                self._current_token.data += self._current_input_char
            else:
                self._current_token.data = self._current_input_char
            return self._continue_in(self.State.Comment)

    def handle_comment_less_than_sign(self) -> TokenizerState:
        self._current_token = cast(HTMLCommentOrCharacter, self._current_token)
        if self._current_input_char == "!":
            self._current_token.data += self._current_input_char
            return self.switch_state_to(self.State.CommentLessThanSignBang)
        elif self._current_input_char == "<":
            self._current_token.data += self._current_input_char
        else:
            return self._reconsume_in(self.State.Comment)

    def handle_comment_less_than_sign_bang(self) -> TokenizerState:
        self._current_token = cast(HTMLCommentOrCharacter, self._current_token)
        if self._current_input_char == "-":
            return self.switch_state_to(self.State.CommentLessThanSignBangDash)
        else:
            return self._reconsume_in(self.State.Comment)

    def handle_comment_less_than_sign_bang_dash(self) -> TokenizerState:
        self._current_token = cast(HTMLCommentOrCharacter, self._current_token)
        if self._current_input_char == "-":
            return self.switch_state_to(self.State.CommentLessThanSignBangDashDash)
        else:
            return self._reconsume_in(self.State.Comment)

    def handle_comment_less_than_sign_bang_dash_dash(self) -> TokenizerState:
        self._current_token = cast(HTMLCommentOrCharacter, self._current_token)
        if self._current_input_char == ">" or self._current_input_char is None:
            return self.switch_state_to(self.State.CommentEnd)
        else:
            return self._reconsume_in(self.State.CommentEnd)

    def handle_comment_end_dash(self) -> TokenizerState:
        self._current_token = cast(HTMLCommentOrCharacter, self._current_token)
        if self._current_input_char == "-":
            return self.switch_state_to(self.State.CommentEnd)
        elif self._current_input_char is None:
            self._append_token_to_queue()
            self._current_token = self._create_new_token(HTMLToken.TokenType.EOF)
            return self._emit_current_token()
        else:
            if self._current_token.data is not None:
                self._current_token.data += "-"
            else:
                self._current_token.data = "-"
            return self._reconsume_in(self.State.Comment)

    def handle_comment_end(self) -> TokenizerState:
        self._current_token = cast(HTMLCommentOrCharacter, self._current_token)
        if self._current_input_char == ">":
            self._append_token_to_queue()
            return self.switch_state_to(self.State.Data)
        elif self._current_input_char == "-":
            if self._current_token.data is not None:
                self._current_token.data += "-"
            else:
                self._current_token.data = "-"
            return self._continue_in(self.State.CommentEnd)
        elif self._current_input_char is None:
            self._append_token_to_queue()
            self._current_token = self._create_new_token(HTMLToken.TokenType.EOF)
            return self._emit_current_token()
        else:
            if self._current_token.data is not None:
                self._current_token.data += "-"
            else:
                self._current_token.data = "-"
            return self._reconsume_in(self.State.Comment)

    def handle_comment_end_bang(self) -> None:
        raise NotImplementedError

    def handle_DOCTYPE(self) -> TokenizerState:
        if char_is_whitespace(self._current_input_char):
            return self.switch_state_to(self.State.BeforeDOCTYPEName)

    def handle_before_DOCTYPE_name(self) -> TokenizerState:
        if char_is_whitespace(self._current_input_char):
            return self._ignore_character_and_continue_to(self.State.BeforeDOCTYPEName)
        else:
            self._current_token = cast(HTMLDoctype, self._create_new_token(HTMLToken.TokenType.DOCTYPE))
            if self._current_token.name is not None and self._current_input_char is not None:
                self._current_token.name += self._current_input_char
            else:
                self._current_token.name = self._current_input_char

            return self.switch_state_to(self.State.DOCTYPEName)

    def handle_DOCTYPE_name(self) -> TokenizerState:
        self._current_token = cast(HTMLDoctype, self._current_token)
        if self._current_input_char == ">":
            self._append_token_to_queue()
            return self.switch_state_to(self.State.Data)
        else:
            self._current_token.name = self._current_token.name + str(self._current_input_char)\
                                        if self._current_token.name else str(self._current_input_char)
            return self._continue_in(self.State.DOCTYPEName)

    def handle_after_DOCTYPE_name(self) -> None:
        raise NotImplementedError

    def handle_after_DOCTYPE_public_keyword(self) -> None:
        raise NotImplementedError

    def handle_before_DOCTYPE_public_identifier(self) -> None:
        raise NotImplementedError

    def handle_DOCTYPE_public_identifier_double_quoted(self) -> None:
        raise NotImplementedError

    def handle_DOCTYPE_public_identifier_single_quoted(self) -> None:
        raise NotImplementedError

    def handle_after_DOCTYPE_public_identifier(self) -> None:
        raise NotImplementedError

    def handle_between_DOCTYPE_public_and_system_identifiers(self) -> None:
        raise NotImplementedError

    def handle_after_DOCTYPE_system_keyword(self) -> None:
        raise NotImplementedError

    def handle_before_DOCTYPE_system_identifier(self) -> None:
        raise NotImplementedError

    def handle_DOCTYPE_system_identifier_double_quoted(self) -> None:
        raise NotImplementedError

    def handle_DOCTYPE_system_identifier_single_quoted(self) -> None:
        raise NotImplementedError

    def handle_after_DOCTYPE_system_identifier(self) -> None:
        raise NotImplementedError

    def handle_bogus_DOCTYPE(self) -> None:
        raise NotImplementedError

    def handle_CDATA_section(self) -> None:
        raise NotImplementedError

    def handle_CDATA_section_bracket(self) -> None:
        raise NotImplementedError

    def handle_CDATA_section_end(self) -> None:
        raise NotImplementedError

    # 13.2.5.72 Character reference state, https://html.spec.whatwg.org/multipage/parsing.html#character-reference-state
    def handle_character_reference(self) -> TokenizerState:
        self._temporary_buffer.append("&")
        self._return_state = cast(HTMLTokenizer.State, self._return_state)

        def else_case():
            self._flush_temporary_buffer()
            return self._reconsume_in_return_state()

        if self._current_input_char is None:
            self._current_token = self._create_new_token(HTMLToken.TokenType.EOF)
            self._append_token_to_queue()
            return else_case()

        if self._current_input_char.isalnum():
            return self._reconsume_in(self.State.NamedCharacterReference)
        elif self._current_input_char == "#":
            self._temporary_buffer.append(self._current_input_char)
            return self.switch_state_to(self.State.NumericCharacterReference)
        else:
            return else_case()

    def handle_named_character_reference(self) -> TokenizerState:
        self._return_state = cast(HTMLTokenizer.State, self._return_state)
        consumed_characters: List[str] = [self._current_input_char]
        while atLeastOneNameStartsWith("".join(consumed_characters)):
            next_char = self._next_code_point()
            if next_char is not None:
                self._current_input_char = next_char
                consumed_characters.append(next_char)
                if next_char == ";":
                    break
        match = getNamedCharFromTable("".join(consumed_characters))
        if match is not None:
            # TODO: Implement case.
            if self._current_token is not None:
                self._current_token = cast(HTMLTag, self._current_token)
                for match_item in match:
                    self._current_token.add_char_to_attribute_value(chr(match_item))
            else:
                self._current_token = cast(HTMLCommentOrCharacter,
                                            self._create_new_token(HTMLToken.TokenType.Character))
                for match_item in match:
                    self._current_token.data = self._current_token.data + chr(match_item)\
                                                if self._current_token.data is not None else chr(match_item)
                return self._emit_current_token()
            return self.switch_state_to(self._return_state)
        else:
            self._temporary_buffer.extend(consumed_characters)
            self._flush_temporary_buffer()
            return self._reconsume_in(self.State.AmbiguousAmpersand)

    def handle_ambiguous_ampersand(self) -> TokenizerState:
        self._return_state = cast(HTMLTokenizer.State, self._return_state)
        if self._current_input_char.isalnum():
            self._temporary_buffer.append(self._current_input_char)
            self._flush_temporary_buffer()
        elif self._current_input_char == ";":
            return self._reconsume_in_return_state()
        else:
            return self._reconsume_in_return_state()

    def handle_numeric_character_reference(self) -> TokenizerState:
        if self._current_input_char == "X" or self._current_input_char == "x":
            self._temporary_buffer.append(self._current_input_char)
            return self.switch_state_to(self.State.HexadecimalCharacterReferenceStart)
        else:
            return self._reconsume_in(self.State.DecimalCharacterReferenceStart)

    def handle_hexadecimal_character_reference_start(self) -> TokenizerState:
        if all(c in string.hexdigits for c in self._current_input_char):
            return self._reconsume_in(self.State.DecimalCharacterReference)
        else:
            raise NotImplementedError

    def handle_decimal_character_reference_start(self) -> TokenizerState:
        if self._current_input_char.isdigit():
            return self._reconsume_in(self.State.DecimalCharacterReference)
        else:
            # TODO: handle parse error.
            self._flush_temporary_buffer()
            if self._return_state is not None:
                return self._reconsume_in_return_state()

    def handle_hexadecimal_character_reference(self) -> TokenizerState:
        if self._current_input_char.isdigit():
            self._character_reference_code *= 16
            self._character_reference_code += ord(self._current_input_char) - 0x0030
        elif char_is_uppercase_alpha(self._current_input_char):
            self._character_reference_code *= 16
            self._character_reference_code += ord(self._current_input_char) - 0x0037
        elif char_is_lowercase_alpha(self._current_input_char):
            self._character_reference_code *= 16
            self._character_reference_code += ord(self._current_input_char) - 0x0057
        elif self._current_input_char == ";":
            return self.switch_state_to(self.State.NumericCharacterReferenceEnd)
        else:
            # TODO: Handle parse error.
            return self._reconsume_in(self.State.NumericCharacterReferenceEnd)

    def handle_decimal_character_reference(self) -> TokenizerState:
        if self._current_input_char.isdigit():
            self._character_reference_code *= 10
            self._character_reference_code += ord(self._current_input_char) - 0x0030
        elif self._current_input_char == ";":
            return self.switch_state_to(self.State.NumericCharacterReferenceEnd)
        else:
            return self._reconsume_in(self.State.NumericCharacterReferenceEnd)

    def handle_numeric_character_reference_end(self) -> TokenizerState:
        if self._character_reference_code == 0:
            # TODO: handle parse error.
            self._character_reference_code = 0xFFFD
        elif self._character_reference_code > 0x10ffff:
            # TODO: handle parse error.
            self._character_reference_code = 0xFFFD
        elif char_is_surrogate(self._character_reference_code):
            # TODO: handle parse error.
            self._character_reference_code = 0xFFFD
        elif char_is_noncharacter(self._character_reference_code):
            # TODO: Handle parse error.
            self._character_reference_code = 0x27
            pass
        elif self._character_reference_code == 0x0D or (
                char_is_control(self._character_reference_code) and not
                char_is_whitespace(chr(self._character_reference_code))):

            conversion_table = {
                0x80: 0x20AC,
                0x82: 0x201A,
                0x83: 0x0192,
                0x84: 0x201E,
                0x85: 0x2026,
                0x86: 0x2020,
                0x87: 0x2021,
                0x88: 0x02C6,
                0x89: 0x2030,
                0x8A: 0x0160,
                0x8B: 0x2039,
                0x8C: 0x0152,
                0x8E: 0x017D,
                0x91: 0x2018,
                0x92: 0x2019,
                0x93: 0x201C,
                0x94: 0x201D,
                0x95: 0x2022,
                0x96: 0x2013,
                0x97: 0x2014,
                0x98: 0x02DC,
                0x99: 0x2122,
                0x9A: 0x0161,
                0x9B: 0x203A,
                0x9C: 0x0153,
                0x9E: 0x017E,
                0x9F: 0x0178,
            }
            value = conversion_table.get(self._character_reference_code, None)
            if value is not None:
                self._character_reference_code = value

        self._temporary_buffer = []
        self._temporary_buffer.append(chr(self._character_reference_code))
        self._flush_temporary_buffer()
        if self._return_state is not None:
            return self._reconsume_in_return_state()

    def _get_state_switcher(self) -> Callable[[], Union[TokenizerState]]:

        switcher = {
            HTMLTokenizer.State.Data: self.handle_data,
            HTMLTokenizer.State.RCDATA: self.handle_RCDATA,
            HTMLTokenizer.State.RAWTEXT: self.handle_RAWTEXT,
            HTMLTokenizer.State.ScriptData: self.handle_script_data,
            HTMLTokenizer.State.PLAINTEXT: self.handle_PLAINTEXT,
            HTMLTokenizer.State.TagOpen: self.handle_tag_open,
            HTMLTokenizer.State.EndTagOpen: self.handle_end_tag_open,
            HTMLTokenizer.State.TagName: self.handle_tag_name,
            HTMLTokenizer.State.RCDATALessThanSign: self.handle_RCDATA_less_than_sign,
            HTMLTokenizer.State.RCDATAEndTagOpen: self.handle_RCDATA_end_tag_open,
            HTMLTokenizer.State.RCDATAEndTagName: self.handle_RCDATA_end_tag_name,
            HTMLTokenizer.State.RAWTEXTLessThanSign: self.handle_RAWTEXT_less_than_sign,
            HTMLTokenizer.State.RAWTEXTEndTagOpen: self.handle_RAWTEXT_end_tag_open,
            HTMLTokenizer.State.RAWTEXTEndTagName: self.handle_RAWTEXT_end_tag_name,
            HTMLTokenizer.State.ScriptDataLessThanSign: self.handle_script_data_less_than_sign,
            HTMLTokenizer.State.ScriptDataEndTagOpen: self.handle_script_data_end_tag_open,
            HTMLTokenizer.State.ScriptDataEndTagName: self.handle_script_data_end_tag_name,
            HTMLTokenizer.State.ScriptDataEscapeStart: self.handle_script_data_escape_start,
            HTMLTokenizer.State.ScriptDataEscapeStartDash: self.handle_script_data_escape_start_dash,
            HTMLTokenizer.State.ScriptDataEscaped: self.handle_script_data_escaped,
            HTMLTokenizer.State.ScriptDataEscapedDash: self.handle_script_data_escaped_dash,
            HTMLTokenizer.State.ScriptDataEscapedDashDash: self.handle_script_data_escaped_dash_dash,
            HTMLTokenizer.State.ScriptDataEscapedLessThanSign: self.handle_script_data_escaped_less_than_sign,
            HTMLTokenizer.State.ScriptDataEscapedEndTagOpen: self.handle_script_data_escaped_end_tag_open,
            HTMLTokenizer.State.ScriptDataEscapedEndTagName: self.handle_script_data_escaped_end_tag_name,
            HTMLTokenizer.State.ScriptDataDoubleEscapeStart: self.handle_script_data_double_escape_start,
            HTMLTokenizer.State.ScriptDataDoubleEscaped: self.handle_script_data_double_escaped,
            HTMLTokenizer.State.ScriptDataDoubleEscapedDash: self.handle_script_data_double_escaped_dash,
            HTMLTokenizer.State.ScriptDataDoubleEscapedDashDash: self.handle_script_data_double_escaped_dash_dash,
            HTMLTokenizer.State.ScriptDataDoubleEscapedLessThanSign: self.handle_script_data_double_escaped_less_than_sign,
            HTMLTokenizer.State.ScriptDataDoubleEscapeEnd: self.handle_script_data_double_escape_end,
            HTMLTokenizer.State.BeforeAttributeName: self.handle_before_attribute_name,
            HTMLTokenizer.State.AttributeName: self.handle_attribute_name,
            HTMLTokenizer.State.AfterAttributeName: self.handle_after_attribute_name,
            HTMLTokenizer.State.BeforeAttributeValue: self.handle_before_attribute_value,
            HTMLTokenizer.State.AttributeValueDoubleQuoted: self.handle_attribute_value_double_quoted,
            HTMLTokenizer.State.AttributeValueSingleQuoted: self.handle_attribute_value_single_quoted,
            HTMLTokenizer.State.AttributeValueUnquoted: self.handle_attribute_value_unquoted,
            HTMLTokenizer.State.AfterAttributeValueQuoted: self.handle_after_attribute_value_quoted,
            HTMLTokenizer.State.SelfClosingStartTag: self.handle_self_closing_start_tag,
            HTMLTokenizer.State.BogusComment: self.handle_bogus_comment,
            HTMLTokenizer.State.MarkupDeclarationOpen: self.handle_markup_declaration_open,
            HTMLTokenizer.State.CommentStart: self.handle_comment_start,
            HTMLTokenizer.State.CommentStartDash: self.handle_comment_start_dash,
            HTMLTokenizer.State.Comment: self.handle_comment,
            HTMLTokenizer.State.CommentLessThanSign: self.handle_comment_less_than_sign,
            HTMLTokenizer.State.CommentLessThanSignBang: self.handle_comment_less_than_sign_bang,
            HTMLTokenizer.State.CommentLessThanSignBangDash: self.handle_comment_less_than_sign_bang_dash,
            HTMLTokenizer.State.CommentLessThanSignBangDashDash: self.handle_comment_less_than_sign_bang_dash_dash,
            HTMLTokenizer.State.CommentEndDash: self.handle_comment_end_dash,
            HTMLTokenizer.State.CommentEnd: self.handle_comment_end,
            HTMLTokenizer.State.CommentEndBang: self.handle_comment_end_bang,
            HTMLTokenizer.State.DOCTYPE: self.handle_DOCTYPE,
            HTMLTokenizer.State.BeforeDOCTYPEName: self.handle_before_DOCTYPE_name,
            HTMLTokenizer.State.DOCTYPEName: self.handle_DOCTYPE_name,
            HTMLTokenizer.State.AfterDOCTYPEName: self.handle_after_DOCTYPE_name,
            HTMLTokenizer.State.AfterDOCTYPEPublicKeyword: self.handle_after_DOCTYPE_public_keyword,
            HTMLTokenizer.State.BeforeDOCTYPEPublicIdentifier: self.handle_before_DOCTYPE_public_identifier,
            HTMLTokenizer.State.DOCTYPEPublicIdentifierDoubleQuoted: self.handle_DOCTYPE_public_identifier_double_quoted,
            HTMLTokenizer.State.DOCTYPEPublicIdentifierSingleQuoted: self.handle_DOCTYPE_public_identifier_single_quoted,
            HTMLTokenizer.State.AfterDOCTYPEPublicIdentifier: self.handle_after_DOCTYPE_public_identifier,
            HTMLTokenizer.State.BetweenDOCTYPEPublicAndSystemIdentifiers: self.handle_between_DOCTYPE_public_and_system_identifiers,
            HTMLTokenizer.State.AfterDOCTYPESystemKeyword: self.handle_after_DOCTYPE_system_keyword,
            HTMLTokenizer.State.BeforeDOCTYPESystemIdentifier: self.handle_before_DOCTYPE_system_identifier,
            HTMLTokenizer.State.DOCTYPESystemIdentifierDoubleQuoted: self.handle_DOCTYPE_system_identifier_double_quoted,
            HTMLTokenizer.State.DOCTYPESystemIdentifierSingleQuoted: self.handle_DOCTYPE_system_identifier_single_quoted,
            HTMLTokenizer.State.AfterDOCTYPESystemIdentifier: self.handle_after_DOCTYPE_system_identifier,
            HTMLTokenizer.State.BogusDOCTYPE: self.handle_bogus_DOCTYPE,
            HTMLTokenizer.State.CDATASection: self.handle_CDATA_section,
            HTMLTokenizer.State.CDATASectionBracket: self.handle_CDATA_section_bracket,
            HTMLTokenizer.State.CDATASectionEnd: self.handle_CDATA_section_end,
            HTMLTokenizer.State.CharacterReference: self.handle_character_reference,
            HTMLTokenizer.State.NamedCharacterReference: self.handle_named_character_reference,
            HTMLTokenizer.State.AmbiguousAmpersand: self.handle_ambiguous_ampersand,
            HTMLTokenizer.State.NumericCharacterReference: self.handle_numeric_character_reference,
            HTMLTokenizer.State.HexadecimalCharacterReferenceStart: self.handle_hexadecimal_character_reference_start,
            HTMLTokenizer.State.DecimalCharacterReferenceStart: self.handle_decimal_character_reference_start,
            HTMLTokenizer.State.HexadecimalCharacterReference: self.handle_hexadecimal_character_reference,
            HTMLTokenizer.State.DecimalCharacterReference: self.handle_decimal_character_reference,
            HTMLTokenizer.State.NumericCharacterReferenceEnd: self.handle_numeric_character_reference_end,
        }

        return switcher.get(self.state, None)

    def run(self) -> None:
        while self._cursor < len(self._html):
            token_point = self._next_code_point()
            if token_point is None:
                self._current_token = self._create_new_token(HTMLToken.TokenType.EOF)
                return self._emit_current_token()
            self._current_input_char = cast(str, token_point)
            switcher = self._get_state_switcher()
            if switcher is not None:
                switcher()

        self._current_token = self._create_new_token(HTMLToken.TokenType.EOF)
        return self._emit_current_token()

    def process_queue(self) -> Optional[HTMLToken]:
        try:
            token = self.queued_tokens.pop()
        except IndexError:
            return None
        else:
            return token

    def next_token(self) -> Optional[HTMLToken]:
        maybe_token = self.process_queue()
        if maybe_token:
            return maybe_token

        if self._current_input_char is None:
            return None

        """
        if token_point is None:
            self._current_token = self._create_new_token(HTMLToken.TokenType.EOF)
            return self._emit_current_token().token
        """

        token_point = self._next_code_point()
        self._current_input_char = cast(str, token_point)

        while True:
            switcher = self._get_state_switcher()
            result = switcher()
            if type(result) == Emit:
                return result.token
            elif type(result) == SwitchTo:
                token_point = self._next_code_point()
                self._current_input_char = cast(str, token_point)
                continue
            elif type(result) == ReConsume:
                continue
            elif type(result) == ReprocessQueue:
                maybe_token = self.process_queue()
                if maybe_token:
                    return maybe_token

                token_point = self._next_code_point()
                self._current_input_char = cast(str, token_point)

