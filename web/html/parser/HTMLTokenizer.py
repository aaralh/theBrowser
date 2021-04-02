from enum import Enum, auto
from typing import Union, Callable, Any, cast, List, Optional
from .HTMLToken import HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter
from .utils import charIsAlpha, charIsControl, charIsNoncharacter, charIsWhitespace, charIsUppercaseAlpha, \
    charIsLowercaseAlpha, charIsSurrogate
from .Entities import getNamedCharFromTable, atLeastOneNameStartsWith


class HTMLTokenizer:

    def __init__(self, html: str, token_handler_cb: Callable[[HTMLToken], None]):
        self.state = self.State.Data
        self.__html = html
        self.__cursor = 0
        self.__current_input_char: str = ""  # TODO: Basically initially is None, fix
        self.__return_state: Union[Any, None] = None
        self.__current_token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter, None] = None
        self.__token_handler_cb: Callable[[HTMLToken], None] = token_handler_cb
        self.__temporary_buffer: List[str] = []
        self.__character_reference_code: int = 0
        self.__last_emitted_start_tag_name: Optional[str] = None

    def __emit_current_token(self) -> None:
        if self.__current_token is not None:
            self.__current_token = cast(HTMLTag, self.__current_token)
            self.__token_handler_cb(self.__current_token)
            if self.__current_token.type == HTMLToken.TokenType.StartTag:
                self.__last_emitted_start_tag_name = self.__current_token.name
            self.__current_token = None
            print("Current state: ", self.state)

    def __create_new_token(
            self, token_type: HTMLToken.TokenType
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

    def __continue_in(self, state: State) -> None:
        self.switch_state_to(state)

    def __ignore_character_and_continue_to(self, new_state: State) -> None:
        self.switch_state_to(new_state)

    def switch_state_to(self, new_state: State) -> None:
        """
        Switch state and consume next character.
        """
        self.state = new_state

    def __reconsume_in(self, new_state: State) -> None:
        """
        Switch state without consuming next character.
        """
        self.state = new_state
        switcher = self.__get_state_switcher()
        if switcher is not None:
            switcher()

    def __next_characters_are(self, characters: str) -> bool:
        for index in range(len(characters)):
            if self.__cursor >= len(self.__html):
                return False
            char = self.__html[self.__cursor + index]
            if char.lower() != characters[index].lower():
                return False

        return True

    def __consume_characters(self, characters: str) -> None:
        self.__cursor += len(characters)

    def __next_code_point(self) -> Union[str, None]:
        if self.__cursor >= len(self.__html):
            return None
        char = self.__html[self.__cursor]
        self.__cursor += 1
        return char

    def __flush_temporary_buffer(self) -> None:
        if self.__current_token is not None:
            self.__current_token = cast(HTMLTag, self.__current_token)
            self.__current_token.addCharToAttributeValue("".join(self.__temporary_buffer))
        else:
            for char in self.__temporary_buffer:
                self.__current_token = cast(HTMLCommentOrCharacter, self.__create_new_token(HTMLToken.TokenType.Character))
                self.__current_token.data = char
                self.__emit_current_token()
        self.__temporary_buffer = []

    def handle_data(self) -> None:
        if self.__current_input_char == "&":
            self.__return_state = self.State.Data
            self.switch_state_to(self.State.CharacterReference)
        elif self.__current_input_char == "<":
            self.switch_state_to(self.State.TagOpen)
        elif self.__current_input_char is None:
            self.__current_token = self.__create_new_token(HTMLToken.TokenType.EOF)
            self.__emit_current_token()
        else:
            self.__current_token = cast(HTMLCommentOrCharacter, self.__create_new_token(HTMLToken.TokenType.Character))
            self.__current_token.data = self.__current_input_char
            self.__continue_in(self.State.Data)
            self.__emit_current_token()

    def handle_RCDATA(self) -> None:
        if self.__current_input_char == "&":
            self.__return_state = self.State.RCDATA
            self.switch_state_to(self.State.CharacterReference)
        elif self.__current_input_char == "<":
            self.switch_state_to(self.State.RCDATALessThanSign)
        elif self.__current_input_char is None:
            self.__current_token = self.__create_new_token(HTMLToken.TokenType.EOF)
            self.__emit_current_token()
        else:
            self.__current_token = cast(HTMLCommentOrCharacter, self.__create_new_token(HTMLToken.TokenType.Character))
            self.__current_token.data = self.__current_input_char
            self.__emit_current_token()

    def handle_RAWTEXT(self) -> None:
        if self.__current_input_char == "<":
            self.switch_state_to(self.State.RAWTEXTLessThanSign)
        elif self.__current_input_char is None:
            self.__current_token = self.__create_new_token(HTMLToken.TokenType.EOF)
            self.__emit_current_token()
        else:
            self.__current_token = cast(HTMLCommentOrCharacter, self.__create_new_token(HTMLToken.TokenType.Character))
            self.__current_token.data = self.__current_input_char
            self.__emit_current_token()

    def handle_script_data(self) -> None:
        if self.__current_input_char == "<":
            self.switch_state_to(self.State.ScriptDataLessThanSign)
        elif self.__current_input_char is None:
            self.__current_token = self.__create_new_token(HTMLToken.TokenType.EOF)
            self.__emit_current_token()
        else:
            self.__current_token = cast(HTMLCommentOrCharacter, self.__create_new_token(HTMLToken.TokenType.Character))
            self.__current_token.data = self.__current_input_char
            self.__emit_current_token()

    def handle_PLAINTEXT(self) -> None:
        raise NotImplementedError

    def handle_tag_open(self) -> None:
        if self.__current_input_char == "!":
            self.__reconsume_in(self.State.MarkupDeclarationOpen)
        elif self.__current_input_char == "/":
            self.switch_state_to(self.State.EndTagOpen)
        elif self.__current_input_char.isalpha():
            self.__current_token = cast(HTMLTag, self.__create_new_token(HTMLToken.TokenType.StartTag))
            self.__reconsume_in(self.State.TagName)

    def handle_end_tag_open(self) -> None:
        self.__current_token = self.__create_new_token(HTMLToken.TokenType.EndTag)
        self.__reconsume_in(self.State.TagName)

    def handle_tag_name(self) -> None:
        if self.__current_input_char is None:
            self.__current_token = self.__create_new_token(HTMLToken.TokenType.EOF)
            self.__emit_current_token()
        elif charIsWhitespace(self.__current_input_char):
            self.switch_state_to(self.State.BeforeAttributeName)
        elif self.__current_input_char == ">":
            self.switch_state_to(self.State.Data)
            self.__emit_current_token()
        else:
            self.__current_token = cast(HTMLTag, self.__current_token)
            if self.__current_token.name is not None and self.__current_input_char is not None:
                self.__current_token.name += self.__current_input_char
            else:
                self.__current_token.name = self.__current_input_char
            self.__continue_in(self.State.TagName)

    def handle_RCDATA_less_than_sign(self) -> None:
        if self.__current_input_char == "/":
            self.__temporary_buffer = []
            self.switch_state_to(self.State.RCDATAEndTagOpen)
        else:
            self.__current_token = cast(HTMLCommentOrCharacter, self.__create_new_token(HTMLToken.TokenType.Character))
            self.__current_token.data = "<"
            self.__emit_current_token()
            self.__reconsume_in(self.State.RCDATA)

    def handle_RCDATA_end_tag_open(self) -> None:
        if charIsAlpha(self.__current_input_char):
            self.__current_token = self.__create_new_token(HTMLToken.TokenType.EndTag)
            self.__current_token = cast(HTMLTag, self.__current_token)
            self.__current_token.name = ""
            self.__reconsume_in(self.State.RCDATAEndTagName)
        else:
            self.__current_token = cast(HTMLCommentOrCharacter, self.__create_new_token(HTMLToken.TokenType.Character))
            self.__current_token.data = "<"
            self.__emit_current_token()
            self.__current_token = cast(HTMLCommentOrCharacter, self.__create_new_token(HTMLToken.TokenType.Character))
            self.__current_token.data = "/"
            self.__emit_current_token()
            self.__reconsume_in(self.State.RCDATA)

    def handle_RCDATA_end_tag_name(self) -> None:
        print("Current char:", self.__current_input_char)
        print("Current token:", self.__current_token)
        print("Last emited token:", self.__last_emitted_start_tag_name)
        self.__current_token = cast(HTMLTag, self.__current_token)

        def elseCase() -> None:
            self.__current_token = cast(HTMLCommentOrCharacter, self.__create_new_token(HTMLToken.TokenType.Character))
            self.__current_token.data = "<"
            self.__emit_current_token()
            self.__current_token = cast(HTMLCommentOrCharacter, self.__create_new_token(HTMLToken.TokenType.Character))
            self.__current_token.data = "/"
            self.__emit_current_token()

            for char in self.__temporary_buffer:
                self.__current_token = cast(HTMLCommentOrCharacter,
                                            self.__create_new_token(HTMLToken.TokenType.Character))
                self.__current_token.data = char
                self.__emit_current_token()
            self.__reconsume_in(self.State.RCDATA)

        if charIsWhitespace(self.__current_input_char):
            if self.__current_token.name == self.__last_emitted_start_tag_name:
                self.switch_state_to(self.State.BeforeAttributeName)
            else:
                elseCase()
        elif self.__current_input_char == "/":
            if self.__current_token.name == self.__last_emitted_start_tag_name:
                self.switch_state_to(self.State.SelfClosingStartTag)
            else:
                elseCase()
        elif self.__current_input_char == ">":
            if self.__current_token.name == self.__last_emitted_start_tag_name:
                self.switch_state_to(self.State.Data)
                self.__emit_current_token()
            else:
                elseCase()
        elif charIsUppercaseAlpha(self.__current_input_char):
            self.__current_token.appendCharToTokenName(self.__current_input_char.lower())
            self.__temporary_buffer.append(self.__current_input_char)
        elif charIsLowercaseAlpha(self.__current_input_char):
            self.__current_token.appendCharToTokenName(self.__current_input_char)
            self.__temporary_buffer.append(self.__current_input_char)
        else:
            elseCase()

    def handle_RAWTEXT_less_than_sign(self) -> None:
        if self.__current_input_char == "/":
            self.__temporary_buffer = []
            self.switch_state_to(self.State.RAWTEXTEndTagOpen)
        else:
            self.__current_token = cast(HTMLCommentOrCharacter, self.__create_new_token(HTMLToken.TokenType.Character))
            self.__current_token.data = "<"
            self.__emit_current_token()
            self.__reconsume_in(self.State.RAWTEXT)

    def handle_RAWTEXT_end_tag_open(self) -> None:
        if charIsAlpha(self.__current_input_char):
            self.__current_token = self.__create_new_token(HTMLToken.TokenType.EndTag)
            self.__current_token = cast(HTMLTag, self.__current_token)
            self.__current_token.name = ""
            self.__reconsume_in(self.State.RAWTEXTEndTagName)
        else:
            self.__current_token = cast(HTMLCommentOrCharacter, self.__create_new_token(HTMLToken.TokenType.Character))
            self.__current_token.data = "<"
            self.__emit_current_token()
            self.__current_token = cast(HTMLCommentOrCharacter, self.__create_new_token(HTMLToken.TokenType.Character))
            self.__current_token.data = "/"
            self.__emit_current_token()
            self.__reconsume_in(self.State.RAWTEXT)

    def handle_RAWTEXT_end_tag_name(self) -> None:
        self.__current_token = cast(HTMLTag, self.__current_token)

        def elseCase() -> None:
            self.__current_token = cast(HTMLCommentOrCharacter, self.__create_new_token(HTMLToken.TokenType.Character))
            self.__current_token.data = "<"
            self.__emit_current_token()
            self.__current_token = cast(HTMLCommentOrCharacter, self.__create_new_token(HTMLToken.TokenType.Character))
            self.__current_token.data = "/"
            self.__emit_current_token()

            for char in self.__temporary_buffer:
                self.__current_token = cast(HTMLCommentOrCharacter,
                                            self.__create_new_token(HTMLToken.TokenType.Character))
                self.__current_token.data = char
                self.__emit_current_token()
            self.__reconsume_in(self.State.RAWTEXT)

        if charIsWhitespace(self.__current_input_char):
            if self.__current_token.name == self.__last_emitted_start_tag_name:
                self.switch_state_to(self.State.BeforeAttributeName)
            else:
                elseCase()
        elif self.__current_input_char == "/":
            if self.__current_token.name == self.__last_emitted_start_tag_name:
                self.switch_state_to(self.State.SelfClosingStartTag)
            else:
                elseCase()
        elif self.__current_input_char == ">":
            if self.__current_token.name == self.__last_emitted_start_tag_name:
                self.switch_state_to(self.State.Data)
                self.__emit_current_token()
            else:
                elseCase()
        elif charIsUppercaseAlpha(self.__current_input_char):
            self.__current_token.appendCharToTokenName(self.__current_input_char.lower())
            self.__temporary_buffer.append(self.__current_input_char)
        elif charIsLowercaseAlpha(self.__current_input_char):
            self.__current_token.appendCharToTokenName(self.__current_input_char)
            self.__temporary_buffer.append(self.__current_input_char)
        else:
            elseCase()

    def handle_script_data_less_than_sign(self) -> None:
        if self.__current_input_char == "/":
            self.__temporary_buffer = []
            self.switch_state_to(self.State.ScriptDataEndTagOpen)
        elif self.__current_input_char == "!":
            self.switch_state_to(self.State.ScriptDataEscapeStart)
            self.__current_token = cast(HTMLCommentOrCharacter, self.__create_new_token(HTMLToken.TokenType.Character))
            self.__current_token.data = "<"
            self.__emit_current_token()
            self.__current_token = cast(HTMLCommentOrCharacter, self.__create_new_token(HTMLToken.TokenType.Character))
            self.__current_token.data = "!"
            self.__emit_current_token()
        else:
            self.__current_token = cast(HTMLCommentOrCharacter, self.__create_new_token(HTMLToken.TokenType.Character))
            self.__current_token.data = "<"
            self.__emit_current_token()
            self.__reconsume_in(self.State.ScriptData)

    def handle_script_data_end_tag_open(self) -> None:
        if charIsUppercaseAlpha(self.__current_input_char) or charIsLowercaseAlpha(self.__current_input_char):
            self.__current_token = cast(HTMLTag, self.__create_new_token(HTMLToken.TokenType.EndTag))
            self.__current_token.name = ""
            self.__reconsume_in(self.State.ScriptDataEndTagName)
        else:
            self.__current_token = cast(HTMLCommentOrCharacter, self.__create_new_token(HTMLToken.TokenType.Character))
            self.__current_token.data = "<"
            self.__emit_current_token()
            self.__current_token = cast(HTMLCommentOrCharacter, self.__create_new_token(HTMLToken.TokenType.Character))
            self.__current_token.data = "/"
            self.__emit_current_token()
            self.__reconsume_in(self.State.ScriptData)

    def handle_script_data_end_tag_name(self) -> None:
        self.__current_token = cast(HTMLTag, self.__current_token)

        def elseCase() -> None:
            self.__current_token = cast(HTMLCommentOrCharacter, self.__create_new_token(HTMLToken.TokenType.Character))
            self.__current_token.data = "<"
            self.__emit_current_token()
            self.__current_token = cast(HTMLCommentOrCharacter, self.__create_new_token(HTMLToken.TokenType.Character))
            self.__current_token.data = "/"
            self.__emit_current_token()
            for char in self.__temporary_buffer:
                self.__current_token = cast(HTMLCommentOrCharacter,
                                            self.__create_new_token(HTMLToken.TokenType.Character))
                self.__current_token.data = char
                self.__emit_current_token()
            self.__reconsume_in(self.State.ScriptData)

        if charIsWhitespace(self.__current_input_char):
            if self.__current_token.name == self.__last_emitted_start_tag_name:
                self.switch_state_to(self.State.BeforeAttributeName)
            else:
                elseCase()
        elif self.__current_input_char == "/":
            if self.__current_token.name == self.__last_emitted_start_tag_name:
                self.switch_state_to(self.State.SelfClosingStartTag)
            else:
                elseCase()
        elif self.__current_input_char == ">":
            if self.__current_token.name == self.__last_emitted_start_tag_name:
                self.switch_state_to(self.State.Data)
                self.__emit_current_token()
            else:
                elseCase()
        elif charIsUppercaseAlpha(self.__current_input_char):
            self.__current_token.appendCharToTokenName(self.__current_input_char.lower())
            self.__temporary_buffer.append(self.__current_input_char)
        elif charIsLowercaseAlpha(self.__current_input_char):
            self.__current_token.appendCharToTokenName(self.__current_input_char)
            self.__temporary_buffer.append(self.__current_input_char)
        else:
            elseCase()

    def handle_script_data_escape_start(self) -> None:
        raise NotImplementedError

    def handle_script_data_escape_start_dash(self) -> None:
        raise NotImplementedError

    def handle_script_data_escaped(self) -> None:
        raise NotImplementedError

    def handle_script_data_escaped_dash(self) -> None:
        raise NotImplementedError

    def handle_script_data_escaped_dash_dash(self) -> None:
        raise NotImplementedError

    def handle_script_data_escaped_less_than_sign(self) -> None:
        raise NotImplementedError

    def handle_script_data_escaped_end_tag_open(self) -> None:
        raise NotImplementedError

    def handle_script_data_escaped_end_tag_name(self) -> None:
        raise NotImplementedError

    def handle_script_data_double_escape_start(self) -> None:
        raise NotImplementedError

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

    def handle_before_attribute_name(self) -> None:
        self.__current_token = cast(HTMLTag, self.__current_token)

        if self.__current_input_char is None:
            self.__reconsume_in(self.State.AfterAttributeName)
        elif charIsWhitespace(self.__current_input_char):
            self.__continue_in(self.State.BeforeAttributeName)
        else:
            self.__current_token.createNewAttribute()
            self.__reconsume_in(self.State.AttributeName)

    def handle_attribute_name(self) -> None:
        self.__current_token = cast(HTMLTag, self.__current_token)

        if (
                self.__current_input_char is None
                or charIsWhitespace(self.__current_input_char)
                or self.__current_input_char == "/"
                or self.__current_input_char == ">"
        ):
            self.__reconsume_in(self.State.AfterAttributeName)
        elif self.__current_input_char == "=":
            self.switch_state_to(self.State.BeforeAttributeValue)
        elif self.__current_input_char.isupper() and self.__current_input_char.isalpha():
            self.__current_token.addCharToAttributeName(self.__current_input_char.lower())
        else:
            self.__current_token.addCharToAttributeName(self.__current_input_char)
            self.__continue_in(self.State.AttributeName)

    def handle_after_attribute_name(self) -> None:
        self.__current_token = cast(HTMLTag, self.__current_token)

        if charIsWhitespace(self.__current_input_char):
            pass
        elif self.__current_input_char == "/":
            self.switch_state_to(self.State.SelfClosingStartTag)
        elif self.__current_input_char == "=":
            self.switch_state_to(self.State.BeforeAttributeValue)
        elif self.__current_input_char == ">":
            self.switch_state_to(self.State.Data)
            self.__emit_current_token()
        elif self.__current_input_char is None:
            raise NotImplementedError
        else:
            self.__current_token.createNewAttribute()
            self.__reconsume_in(self.State.AttributeName)

    def handle_before_attribute_value(self) -> None:
        if charIsWhitespace(self.__current_input_char):
            self.__continue_in(self.State.BeforeAttributeValue)
        elif self.__current_input_char == '"':
            self.switch_state_to(self.State.AttributeValueDoubleQuoted)
        elif self.__current_input_char == "'":
            self.switch_state_to(self.State.AttributeValueSingleQuoted)
        elif self.__current_input_char == ">":
            self.switch_state_to(self.State.Data)
            self.__emit_current_token()
        else:
            self.__reconsume_in(self.State.AttributeValueUnquoted)

    def handle_attribute_value_double_quoted(self) -> None:
        self.__current_token = cast(HTMLTag, self.__current_token)
        if self.__current_input_char is None:
            self.__current_token = self.__create_new_token(HTMLToken.TokenType.EOF)
            self.__emit_current_token()
        elif self.__current_input_char == '"':
            self.switch_state_to(self.State.AfterAttributeValueQuoted)
        elif self.__current_input_char == "&":
            self.__return_state = self.State.AttributeValueDoubleQuoted
            self.switch_state_to(self.State.CharacterReference)
        else:
            self.__current_token.addCharToAttributeValue(self.__current_input_char)
            self.__continue_in(self.State.AttributeValueDoubleQuoted)

    def handle_attribute_value_single_quoted(self) -> None:
        self.__current_token = cast(HTMLTag, self.__current_token)
        if self.__current_input_char is None:
            self.__current_token = self.__create_new_token(HTMLToken.TokenType.EOF)
            self.__emit_current_token()
        elif self.__current_input_char == "'":
            self.switch_state_to(self.State.AfterAttributeValueQuoted)
        elif self.__current_input_char == "&":
            self.__return_state = self.State.AttributeValueSingleQuoted
            self.switch_state_to(self.State.CharacterReference)
        else:
            self.__current_token.addCharToAttributeValue(self.__current_input_char)
            self.__continue_in(self.State.AttributeValueSingleQuoted)

    def handle_attribute_value_unquoted(self) -> None:
        self.__current_token = cast(HTMLTag, self.__current_token)
        if self.__current_input_char is None:
            self.__current_token = self.__create_new_token(HTMLToken.TokenType.EOF)
            self.__emit_current_token()
        elif charIsWhitespace(self.__current_input_char):
            self.switch_state_to(self.State.BeforeAttributeName)
        elif self.__current_input_char == "&":
            self.__return_state = self.State.AttributeValueUnquoted
            self.switch_state_to(self.State.CharacterReference)
        elif self.__current_input_char == ">":
            self.switch_state_to(self.State.Data)
            self.__emit_current_token()
        else:
            self.__current_token.addCharToAttributeValue(self.__current_input_char)
            self.__continue_in(self.State.AttributeValueUnquoted)

    def handle_after_attribute_value_quoted(self) -> None:
        if self.__current_input_char is None:
            self.__current_token = self.__create_new_token(HTMLToken.TokenType.EOF)
            self.__emit_current_token()
        elif charIsWhitespace(self.__current_input_char):
            self.switch_state_to(self.State.BeforeAttributeName)
        elif self.__current_input_char == "/":
            self.switch_state_to(self.State.SelfClosingStartTag)
        elif self.__current_input_char == ">":
            self.switch_state_to(self.State.Data)
            self.__emit_current_token()
        else:
            self.__reconsume_in(self.State.BeforeAttributeName)

    def handle_self_closing_start_tag(self) -> None:
        self.__current_token = cast(HTMLTag, self.__current_token)
        if self.__current_input_char == ">":
            self.__current_token.selfClosing = True
            self.switch_state_to(self.State.Data)
            self.__emit_current_token()
        elif self.__current_input_char is None:
            self.__current_token = self.__create_new_token(HTMLToken.TokenType.EOF)
            self.__emit_current_token()
        else:
            self.__reconsume_in(self.State.BeforeAttributeName)

    def handle_bogus_comment(self) -> None:
        raise NotImplementedError

    def handle_markup_declaration_open(self) -> None:
        if self.__next_characters_are("--"):
            self.__consume_characters("--")
            self.__current_token = self.__create_new_token(HTMLToken.TokenType.Comment)
            self.switch_state_to(self.State.CommentStart)
        elif self.__next_characters_are("DOCTYPE"):
            self.__consume_characters("DOCTYPE")
            self.switch_state_to(self.State.DOCTYPE)

    def handle_comment_start(self) -> None:

        if self.__current_input_char == "-":
            self.switch_state_to(self.State.CommentStartDash)
        elif self.__current_input_char == ">":
            self.switch_state_to(self.State.Data)
            self.__emit_current_token()
        else:
            self.__reconsume_in(self.State.Comment)

    def handle_comment_start_dash(self) -> None:
        self.__current_token = cast(HTMLCommentOrCharacter, self.__current_token)
        if self.__current_input_char == "-":
            self.switch_state_to(self.State.CommentEnd)
        elif self.__current_input_char == ">":
            self.switch_state_to(self.State.Data)
            self.__emit_current_token()
        elif self.__current_input_char is None:
            self.__emit_current_token()
            self.__current_token = self.__create_new_token(HTMLToken.TokenType.EOF)
            self.__emit_current_token()
        else:
            if self.__current_token.data is not None:
                self.__current_token.data += "-"
            else:
                self.__current_token.data = "-"
            self.__reconsume_in(self.State.Comment)

    def handle_comment(self) -> None:
        self.__current_token = cast(HTMLCommentOrCharacter, self.__current_token)
        if self.__current_input_char == "-":
            self.switch_state_to(self.State.CommentEndDash)
        elif self.__current_input_char is None:
            self.__emit_current_token()
            self.__current_token = self.__create_new_token(HTMLToken.TokenType.EOF)
            self.__emit_current_token()
        else:
            if self.__current_token.data is not None:
                self.__current_token.data += self.__current_input_char
            else:
                self.__current_token.data = self.__current_input_char
            self.__continue_in(self.State.Comment)

    def handle_comment_less_than_sign(self) -> None:
        raise NotImplementedError

    def handle_comment_less_than_sign_bang(self) -> None:
        raise NotImplementedError

    def handle_comment_less_than_sign_bang_dash(self) -> None:
        raise NotImplementedError

    def handle_comment_less_than_sign_bang_dash_dash(self) -> None:
        raise NotImplementedError

    def handle_comment_end_dash(self) -> None:
        self.__current_token = cast(HTMLCommentOrCharacter, self.__current_token)
        if self.__current_input_char == "-":
            self.switch_state_to(self.State.CommentEnd)
        elif self.__current_input_char is None:
            self.__emit_current_token()
            self.__current_token = self.__create_new_token(HTMLToken.TokenType.EOF)
            self.__emit_current_token()
        else:
            if self.__current_token.data is not None:
                self.__current_token.data += "-"
            else:
                self.__current_token.data = "-"
            self.__reconsume_in(self.State.Comment)

    def handle_comment_end(self) -> None:
        self.__current_token = cast(HTMLCommentOrCharacter, self.__current_token)
        if self.__current_input_char == ">":
            self.switch_state_to(self.State.Data)
            self.__emit_current_token()
        elif self.__current_input_char == "-":
            if self.__current_token.data is not None:
                self.__current_token.data += "-"
            else:
                self.__current_token.data = "-"
            self.__continue_in(self.State.CommentEnd)
        elif self.__current_input_char is None:
            self.__emit_current_token()
            self.__current_token = self.__create_new_token(HTMLToken.TokenType.EOF)
            self.__emit_current_token()
        else:
            if self.__current_token.data is not None:
                self.__current_token.data += "-"
            else:
                self.__current_token.data = "-"
            self.__reconsume_in(self.State.Comment)

    def handle_comment_end_bang(self) -> None:
        raise NotImplementedError

    def handle_DOCTYPE(self) -> None:
        if charIsWhitespace(self.__current_input_char):
            self.switch_state_to(self.State.BeforeDOCTYPEName)

    def handle_before_DOCTYPE_name(self) -> None:
        if charIsWhitespace(self.__current_input_char):
            self.__ignore_character_and_continue_to(self.State.BeforeDOCTYPEName)
        else:
            self.__current_token = cast(HTMLDoctype, self.__create_new_token(HTMLToken.TokenType.DOCTYPE))
            if self.__current_token.name is not None and self.__current_input_char is not None:
                self.__current_token.name += self.__current_input_char
            else:
                self.__current_token.name = self.__current_input_char

            self.switch_state_to(self.State.DOCTYPEName)

    def handle_DOCTYPE_name(self) -> None:
        self.__current_token = cast(HTMLDoctype, self.__current_token)
        if self.__current_input_char == ">":
            self.switch_state_to(self.State.Data)
            self.__emit_current_token()
        else:
            self.__current_token.name = self.__current_token.name + str(self.__current_input_char)\
                                        if self.__current_token.name else str(self.__current_input_char)
            self.__continue_in(self.State.DOCTYPEName)

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

    def handle_character_reference(self) -> None:
        self.__temporary_buffer.append("&")
        self.__return_state = cast(HTMLTokenizer.State, self.__return_state)
        if self.__current_input_char.isalnum():
            self.__reconsume_in(self.State.NamedCharacterReference)
        elif self.__current_input_char == "#":
            self.__temporary_buffer.append(self.__current_input_char)
            self.switch_state_to(self.State.NumericCharacterReference)
        else:
            self.__flush_temporary_buffer()
            self.__reconsume_in(self.__return_state)

    def handle_named_character_reference(self) -> None:
        self.__return_state = cast(HTMLTokenizer.State, self.__return_state)
        consumedCharacters: List[str] = [self.__current_input_char]
        while atLeastOneNameStartsWith("".join(consumedCharacters)):
            nextChar = self.__next_code_point()
            if nextChar is not None:
                self.__current_input_char = nextChar
                consumedCharacters.append(nextChar)
                if nextChar == ";":
                    break
        match = getNamedCharFromTable("".join(consumedCharacters))
        if match is not None:
            # TODO: Implement case.
            if self.__current_token is not None:
                self.__current_token = cast(HTMLTag, self.__current_token)
                for match_item in match:
                    self.__current_token.addCharToAttributeValue(chr(match_item))
            else:
                self.__current_token = cast(HTMLCommentOrCharacter,
                                            self.__create_new_token(HTMLToken.TokenType.Character))
                for match_item in match:
                    self.__current_token.data = self.__current_token.data + chr(match_item)\
                                                if self.__current_token.data is not None else chr(match_item)
                self.__emit_current_token()
            self.switch_state_to(self.__return_state)
        else:
            self.__temporary_buffer.extend(consumedCharacters)
            self.__flush_temporary_buffer()
            self.__reconsume_in(self.State.AmbiguousAmpersand)

    def handle_ambiguous_ampersand(self) -> None:
        self.__return_state = cast(HTMLTokenizer.State, self.__return_state)
        if self.__current_input_char.isalnum():
            self.__temporary_buffer.append(self.__current_input_char)
            self.__flush_temporary_buffer()
        elif self.__current_input_char == ";":
            self.__reconsume_in(self.__return_state)
        else:
            self.__reconsume_in(self.__return_state)

    def handle_numeric_character_reference(self) -> None:
        if self.__current_input_char == "X" or self.__current_input_char == "x":
            self.__temporary_buffer.append(self.__current_input_char)
            self.switch_state_to(self.State.HexadecimalCharacterReferenceStart)
        else:
            self.__reconsume_in(self.State.DecimalCharacterReferenceStart)

    def handle_hexadecimal_character_reference_start(self) -> None:
        raise NotImplementedError

    def handle_decimal_character_reference_start(self) -> None:
        if self.__current_input_char.isdigit():
            self.__reconsume_in(self.State.HexadecimalCharacterReference)
        else:
            # TODO: handle parse error.
            self.__flush_temporary_buffer()
            if self.__return_state is not None:
                self.__reconsume_in(self.__return_state)

    def handle_hexadecimal_character_reference(self) -> None:
        if self.__current_input_char.isdigit():
            self.__character_reference_code *= 16
            self.__character_reference_code += ord(self.__current_input_char) - 0x0030
        elif charIsUppercaseAlpha(self.__current_input_char):
            self.__character_reference_code *= 16
            self.__character_reference_code += ord(self.__current_input_char) - 0x0037
        elif charIsLowercaseAlpha(self.__current_input_char):
            self.__character_reference_code *= 16
            self.__character_reference_code += ord(self.__current_input_char) - 0x0057
        elif self.__current_input_char == ";":
            self.switch_state_to(self.State.NumericCharacterReferenceEnd)
        else:
            # TODO: Handle parse error.
            self.__reconsume_in(self.State.NumericCharacterReferenceEnd)

    def handle_decimal_character_reference(self) -> None:
        raise NotImplementedError

    def handle_numeric_character_reference_end(self) -> None:
        if self.__character_reference_code == 0:
            # TODO: handle parse error.
            self.__character_reference_code = 0xFFFD
        elif self.__character_reference_code > 0x10ffff:
            # TODO: handle parse error.
            self.__character_reference_code = 0xFFFD
        elif charIsSurrogate(self.__character_reference_code):
            # TODO: handle parse error.
            self.__character_reference_code = 0xFFFD
        elif charIsNoncharacter(self.__character_reference_code):
            # TODO: Handle parse error.
            pass
        elif self.__character_reference_code == 0x0D or (
                charIsControl(self.__character_reference_code) and not
                charIsWhitespace(chr(self.__character_reference_code))):

            conversionTable = {
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
            value = conversionTable.get(self.__character_reference_code, None)
            if value is not None:
                self.__character_reference_code = value

        self.__temporary_buffer = []
        self.__temporary_buffer.append(chr(self.__character_reference_code))
        self.__flush_temporary_buffer()
        if self.__return_state is not None:
            self.switch_state_to(self.__return_state)

    def __get_state_switcher(self) -> Union[Callable[[], None], None]:

        switcher = {
            self.State.Data: self.handle_data,
            self.State.RCDATA: self.handle_RCDATA,
            self.State.RAWTEXT: self.handle_RAWTEXT,
            self.State.ScriptData: self.handle_script_data,
            self.State.PLAINTEXT: self.handle_PLAINTEXT,
            self.State.TagOpen: self.handle_tag_open,
            self.State.EndTagOpen: self.handle_end_tag_open,
            self.State.TagName: self.handle_tag_name,
            self.State.RCDATALessThanSign: self.handle_RCDATA_less_than_sign,
            self.State.RCDATAEndTagOpen: self.handle_RCDATA_end_tag_open,
            self.State.RCDATAEndTagName: self.handle_RCDATA_end_tag_name,
            self.State.RAWTEXTLessThanSign: self.handle_RAWTEXT_less_than_sign,
            self.State.RAWTEXTEndTagOpen: self.handle_RAWTEXT_end_tag_open,
            self.State.RAWTEXTEndTagName: self.handle_RAWTEXT_end_tag_name,
            self.State.ScriptDataLessThanSign: self.handle_script_data_less_than_sign,
            self.State.ScriptDataEndTagOpen: self.handle_script_data_end_tag_open,
            self.State.ScriptDataEndTagName: self.handle_script_data_end_tag_name,
            self.State.ScriptDataEscapeStart: self.handle_script_data_escape_start,
            self.State.ScriptDataEscapeStartDash: self.handle_script_data_escape_start_dash,
            self.State.ScriptDataEscaped: self.handle_script_data_escaped,
            self.State.ScriptDataEscapedDash: self.handle_script_data_escaped_dash,
            self.State.ScriptDataEscapedDashDash: self.handle_script_data_escaped_dash_dash,
            self.State.ScriptDataEscapedLessThanSign: self.handle_script_data_escaped_less_than_sign,
            self.State.ScriptDataEscapedEndTagOpen: self.handle_script_data_escaped_end_tag_open,
            self.State.ScriptDataEscapedEndTagName: self.handle_script_data_escaped_end_tag_name,
            self.State.ScriptDataDoubleEscapeStart: self.handle_script_data_double_escape_start,
            self.State.ScriptDataDoubleEscaped: self.handle_script_data_double_escaped,
            self.State.ScriptDataDoubleEscapedDash: self.handle_script_data_double_escaped_dash,
            self.State.ScriptDataDoubleEscapedDashDash: self.handle_script_data_double_escaped_dash_dash,
            self.State.ScriptDataDoubleEscapedLessThanSign: self.handle_script_data_double_escaped_less_than_sign,
            self.State.ScriptDataDoubleEscapeEnd: self.handle_script_data_double_escape_end,
            self.State.BeforeAttributeName: self.handle_before_attribute_name,
            self.State.AttributeName: self.handle_attribute_name,
            self.State.AfterAttributeName: self.handle_after_attribute_name,
            self.State.BeforeAttributeValue: self.handle_before_attribute_value,
            self.State.AttributeValueDoubleQuoted: self.handle_attribute_value_double_quoted,
            self.State.AttributeValueSingleQuoted: self.handle_attribute_value_single_quoted,
            self.State.AttributeValueUnquoted: self.handle_attribute_value_unquoted,
            self.State.AfterAttributeValueQuoted: self.handle_after_attribute_value_quoted,
            self.State.SelfClosingStartTag: self.handle_self_closing_start_tag,
            self.State.BogusComment: self.handle_bogus_comment,
            self.State.MarkupDeclarationOpen: self.handle_markup_declaration_open,
            self.State.CommentStart: self.handle_comment_start,
            self.State.CommentStartDash: self.handle_comment_start_dash,
            self.State.Comment: self.handle_comment,
            self.State.CommentLessThanSign: self.handle_comment_less_than_sign,
            self.State.CommentLessThanSignBang: self.handle_comment_less_than_sign_bang,
            self.State.CommentLessThanSignBangDash: self.handle_comment_less_than_sign_bang_dash,
            self.State.CommentLessThanSignBangDashDash: self.handle_comment_less_than_sign_bang_dash_dash,
            self.State.CommentEndDash: self.handle_comment_end_dash,
            self.State.CommentEnd: self.handle_comment_end,
            self.State.CommentEndBang: self.handle_comment_end_bang,
            self.State.DOCTYPE: self.handle_DOCTYPE,
            self.State.BeforeDOCTYPEName: self.handle_before_DOCTYPE_name,
            self.State.DOCTYPEName: self.handle_DOCTYPE_name,
            self.State.AfterDOCTYPEName: self.handle_after_DOCTYPE_name,
            self.State.AfterDOCTYPEPublicKeyword: self.handle_after_DOCTYPE_public_keyword,
            self.State.BeforeDOCTYPEPublicIdentifier: self.handle_before_DOCTYPE_public_identifier,
            self.State.DOCTYPEPublicIdentifierDoubleQuoted: self.handle_DOCTYPE_public_identifier_double_quoted,
            self.State.DOCTYPEPublicIdentifierSingleQuoted: self.handle_DOCTYPE_public_identifier_single_quoted,
            self.State.AfterDOCTYPEPublicIdentifier: self.handle_after_DOCTYPE_public_identifier,
            self.State.BetweenDOCTYPEPublicAndSystemIdentifiers: self.handle_between_DOCTYPE_public_and_system_identifiers,
            self.State.AfterDOCTYPESystemKeyword: self.handle_after_DOCTYPE_system_keyword,
            self.State.BeforeDOCTYPESystemIdentifier: self.handle_before_DOCTYPE_system_identifier,
            self.State.DOCTYPESystemIdentifierDoubleQuoted: self.handle_DOCTYPE_system_identifier_double_quoted,
            self.State.DOCTYPESystemIdentifierSingleQuoted: self.handle_DOCTYPE_system_identifier_single_quoted,
            self.State.AfterDOCTYPESystemIdentifier: self.handle_after_DOCTYPE_system_identifier,
            self.State.BogusDOCTYPE: self.handle_bogus_DOCTYPE,
            self.State.CDATASection: self.handle_CDATA_section,
            self.State.CDATASectionBracket: self.handle_CDATA_section_bracket,
            self.State.CDATASectionEnd: self.handle_CDATA_section_end,
            self.State.CharacterReference: self.handle_character_reference,
            self.State.NamedCharacterReference: self.handle_named_character_reference,
            self.State.AmbiguousAmpersand: self.handle_ambiguous_ampersand,
            self.State.NumericCharacterReference: self.handle_numeric_character_reference,
            self.State.HexadecimalCharacterReferenceStart: self.handle_hexadecimal_character_reference_start,
            self.State.DecimalCharacterReferenceStart: self.handle_decimal_character_reference_start,
            self.State.HexadecimalCharacterReference: self.handle_hexadecimal_character_reference,
            self.State.DecimalCharacterReference: self.handle_decimal_character_reference,
            self.State.NumericCharacterReferenceEnd: self.handle_numeric_character_reference_end,
        }

        return switcher.get(self.state, None)

    def run(self) -> None:
        while self.__cursor < len(self.__html):
            token_point = self.__next_code_point()
            if token_point is None:
                self.__current_token = self.__create_new_token(HTMLToken.TokenType.EOF)
                self.__emit_current_token()
            self.__current_input_char = cast(str, token_point)
            switcher = self.__get_state_switcher()
            if switcher is not None:
                switcher()

        self.__current_token = self.__create_new_token(HTMLToken.TokenType.EOF)
        self.__emit_current_token()

