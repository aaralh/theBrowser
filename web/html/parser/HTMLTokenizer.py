from enum import Enum, auto
from typing import Union, Callable, Any, cast, List, Optional
from .HTMLToken import HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter
from .utils import charIsAlpha, charIsControl, charIsNoncharacter, charIsWhitespace, charIsUppercaseAlpha, \
    charIsLowercaseAlpha, charIsSurrogate
from .Entities import getNamedCharFromTable, atLeastOneNameStartsWith


class HTMLTokenizer:

    def __init__(self, html: str, tokenHandlerCb: Callable[[HTMLToken], None]):
        self.state = self.State.Data
        self.__html = html
        self.__cursor = 0
        self.__currentInputChar: str = ""  # TODO: Basically initially is None, fix
        self.__returnState: Union[Any, None] = None
        self.__currentToken: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter, None] = None
        self.__tokenHandlerCb: Callable[[HTMLToken], None] = tokenHandlerCb
        self.__temporaryBuffer: List[str] = []
        self.__characterReferenceCode: int = 0
        self.__lastEmittedStartTagName: Optional[str] = None

    def __emitCurrentToken(self) -> None:
        if self.__currentToken is not None:
            self.__currentToken = cast(HTMLTag, self.__currentToken)
            self.__tokenHandlerCb(self.__currentToken)
            if self.__currentToken.type == HTMLToken.TokenType.StartTag:
                self.__lastEmittedStartTagName = self.__currentToken.name
            self.__currentToken = None
            print("Current state: ", self.state)

    def __createNewToken(
            self, tokenType: HTMLToken.TokenType
    ) -> Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]:
        token: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]
        if tokenType == HTMLToken.TokenType.DOCTYPE:
            token = HTMLDoctype()
        elif tokenType == HTMLToken.TokenType.Comment or tokenType == HTMLToken.TokenType.Character:
            token = HTMLCommentOrCharacter(tokenType)
        elif tokenType == HTMLToken.TokenType.StartTag or tokenType == HTMLToken.TokenType.EndTag:
            token = HTMLTag(tokenType)
        else:
            token = HTMLToken(tokenType)
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

    def __continueIn(self, state: State) -> None:
        self.switchStateTo(state)

    def __ignoreCharacterAndContinueTo(self, newState: State) -> None:
        self.switchStateTo(newState)

    def switchStateTo(self, newState: State) -> None:
        """
        Switch state and consume next character.
        """
        self.state = newState

    def __reconsumeIn(self, newState: State) -> None:
        """
        Switch state without consuming next character.
        """
        self.state = newState
        switcher = self.__getStateSwitcher()
        if switcher is not None:
            switcher()

    def __nextCharactersAre(self, characters: str) -> bool:
        for index in range(len(characters)):
            if self.__cursor >= len(self.__html):
                return False
            char = self.__html[self.__cursor + index]
            if char.lower() != characters[index].lower():
                return False

        return True

    def __consumeCharacters(self, characters: str) -> None:
        self.__cursor += len(characters)

    def __nextCodePoint(self) -> Union[str, None]:
        if self.__cursor >= len(self.__html):
            return None
        char = self.__html[self.__cursor]
        self.__cursor += 1
        return char

    def __flushTemporaryBuffer(self) -> None:
        if self.__currentToken is not None:
            self.__currentToken = cast(HTMLTag, self.__currentToken)
            self.__currentToken.addCharToAttributeValue("".join(self.__temporaryBuffer))
        else:
            for char in self.__temporaryBuffer:
                self.__currentToken = cast(HTMLCommentOrCharacter, self.__createNewToken(HTMLToken.TokenType.Character))
                self.__currentToken.data = char
                self.__emitCurrentToken()
        self.__temporaryBuffer = []

    def handleData(self) -> None:
        if self.__currentInputChar == "&":
            self.__returnState = self.State.Data
            self.switchStateTo(self.State.CharacterReference)
        elif self.__currentInputChar == "<":
            self.switchStateTo(self.State.TagOpen)
        elif self.__currentInputChar is None:
            self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
            self.__emitCurrentToken()
        else:
            self.__currentToken = cast(HTMLCommentOrCharacter, self.__createNewToken(HTMLToken.TokenType.Character))
            self.__currentToken.data = self.__currentInputChar
            self.__continueIn(self.State.Data)
            self.__emitCurrentToken()

    def handleRCDATA(self) -> None:
        if self.__currentInputChar == "&":
            self.__returnState = self.State.RCDATA
            self.switchStateTo(self.State.CharacterReference)
        elif self.__currentInputChar == "<":
            self.switchStateTo(self.State.RCDATALessThanSign)
        elif self.__currentInputChar is None:
            self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
            self.__emitCurrentToken()
        else:
            self.__currentToken = cast(HTMLCommentOrCharacter, self.__createNewToken(HTMLToken.TokenType.Character))
            self.__currentToken.data = self.__currentInputChar
            self.__emitCurrentToken()

    def handleRAWTEXT(self) -> None:
        if self.__currentInputChar == "<":
            self.switchStateTo(self.State.RAWTEXTLessThanSign)
        elif self.__currentInputChar is None:
            self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
            self.__emitCurrentToken()
        else:
            self.__currentToken = cast(HTMLCommentOrCharacter, self.__createNewToken(HTMLToken.TokenType.Character))
            self.__currentToken.data = self.__currentInputChar
            self.__emitCurrentToken()

    def handleScriptData(self) -> None:
        if self.__currentInputChar == "<":
            self.switchStateTo(self.State.ScriptDataLessThanSign)
        elif self.__currentInputChar is None:
            self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
            self.__emitCurrentToken()
        else:
            self.__currentToken = cast(HTMLCommentOrCharacter, self.__createNewToken(HTMLToken.TokenType.Character))
            self.__currentToken.data = self.__currentInputChar
            self.__emitCurrentToken()

    def handlePLAINTEXT(self) -> None:
        raise NotImplementedError

    def handleTagOpen(self) -> None:
        if self.__currentInputChar == "!":
            self.__reconsumeIn(self.State.MarkupDeclarationOpen)
        elif self.__currentInputChar == "/":
            self.switchStateTo(self.State.EndTagOpen)
        elif self.__currentInputChar.isalpha():
            self.__currentToken = cast(HTMLTag, self.__createNewToken(HTMLToken.TokenType.StartTag))
            self.__reconsumeIn(self.State.TagName)

    def handleEndTagOpen(self) -> None:
        self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EndTag)
        self.__reconsumeIn(self.State.TagName)

    def handleTagName(self) -> None:
        if self.__currentInputChar is None:
            self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
            self.__emitCurrentToken()
        elif charIsWhitespace(self.__currentInputChar):
            self.switchStateTo(self.State.BeforeAttributeName)
        elif self.__currentInputChar == ">":
            self.switchStateTo(self.State.Data)
            self.__emitCurrentToken()
        else:
            self.__currentToken = cast(HTMLTag, self.__currentToken)
            if self.__currentToken.name is not None and self.__currentInputChar is not None:
                self.__currentToken.name += self.__currentInputChar
            else:
                self.__currentToken.name = self.__currentInputChar
            self.__continueIn(self.State.TagName)

    def handleRCDATALessThanSign(self) -> None:
        if self.__currentInputChar == "/":
            self.__temporaryBuffer = []
            self.switchStateTo(self.State.RCDATAEndTagOpen)
        else:
            self.__currentToken = cast(HTMLCommentOrCharacter, self.__createNewToken(HTMLToken.TokenType.Character))
            self.__currentToken.data = "<"
            self.__emitCurrentToken()
            self.__reconsumeIn(self.State.RCDATA)

    def handleRCDATAEndTagOpen(self) -> None:
        if charIsAlpha(self.__currentInputChar):
            self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EndTag)
            self.__currentToken = cast(HTMLTag, self.__currentToken)
            self.__currentToken.name = ""
            self.__reconsumeIn(self.State.RCDATAEndTagName)
        else:
            self.__currentToken = cast(HTMLCommentOrCharacter, self.__createNewToken(HTMLToken.TokenType.Character))
            self.__currentToken.data = "<"
            self.__emitCurrentToken()
            self.__currentToken = cast(HTMLCommentOrCharacter, self.__createNewToken(HTMLToken.TokenType.Character))
            self.__currentToken.data = "/"
            self.__emitCurrentToken()
            self.__reconsumeIn(self.State.RCDATA)

    def handleRCDATAEndTagName(self) -> None:
        print("Current char:", self.__currentInputChar)
        print("Current token:", self.__currentToken)
        print("Last emited token:", self.__lastEmittedStartTagName)
        self.__currentToken = cast(HTMLTag, self.__currentToken)

        def elseCase() -> None:
            self.__currentToken = cast(HTMLCommentOrCharacter, self.__createNewToken(HTMLToken.TokenType.Character))
            self.__currentToken.data = "<"
            self.__emitCurrentToken()
            self.__currentToken = cast(HTMLCommentOrCharacter, self.__createNewToken(HTMLToken.TokenType.Character))
            self.__currentToken.data = "/"
            self.__emitCurrentToken()

            for char in self.__temporaryBuffer:
                self.__currentToken = cast(HTMLCommentOrCharacter,
                                           self.__createNewToken(HTMLToken.TokenType.Character))
                self.__currentToken.data = char
                self.__emitCurrentToken()
            self.__reconsumeIn(self.State.RCDATA)

        if charIsWhitespace(self.__currentInputChar):
            if self.__currentToken.name == self.__lastEmittedStartTagName:
                self.switchStateTo(self.State.BeforeAttributeName)
            else:
                elseCase()
        elif self.__currentInputChar == "/":
            if self.__currentToken.name == self.__lastEmittedStartTagName:
                self.switchStateTo(self.State.SelfClosingStartTag)
            else:
                elseCase()
        elif self.__currentInputChar == ">":
            if self.__currentToken.name == self.__lastEmittedStartTagName:
                self.switchStateTo(self.State.Data)
                self.__emitCurrentToken()
            else:
                elseCase()
        elif charIsUppercaseAlpha(self.__currentInputChar):
            self.__currentToken.appendCharToTokenName(self.__currentInputChar.lower())
            self.__temporaryBuffer.append(self.__currentInputChar)
        elif charIsLowercaseAlpha(self.__currentInputChar):
            self.__currentToken.appendCharToTokenName(self.__currentInputChar)
            self.__temporaryBuffer.append(self.__currentInputChar)
        else:
            elseCase()

    def handleRAWTEXTLessThanSign(self) -> None:
        if self.__currentInputChar == "/":
            self.__temporaryBuffer = []
            self.switchStateTo(self.State.RAWTEXTEndTagOpen)
        else:
            self.__currentToken = cast(HTMLCommentOrCharacter, self.__createNewToken(HTMLToken.TokenType.Character))
            self.__currentToken.data = "<"
            self.__emitCurrentToken()
            self.__reconsumeIn(self.State.RAWTEXT)

    def handleRAWTEXTEndTagOpen(self) -> None:
        if charIsAlpha(self.__currentInputChar):
            self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EndTag)
            self.__currentToken = cast(HTMLTag, self.__currentToken)
            self.__currentToken.name = ""
            self.__reconsumeIn(self.State.RAWTEXTEndTagName)
        else:
            self.__currentToken = cast(HTMLCommentOrCharacter, self.__createNewToken(HTMLToken.TokenType.Character))
            self.__currentToken.data = "<"
            self.__emitCurrentToken()
            self.__currentToken = cast(HTMLCommentOrCharacter, self.__createNewToken(HTMLToken.TokenType.Character))
            self.__currentToken.data = "/"
            self.__emitCurrentToken()
            self.__reconsumeIn(self.State.RAWTEXT)

    def handleRAWTEXTEndTagName(self) -> None:
        self.__currentToken = cast(HTMLTag, self.__currentToken)

        def elseCase() -> None:
            self.__currentToken = cast(HTMLCommentOrCharacter, self.__createNewToken(HTMLToken.TokenType.Character))
            self.__currentToken.data = "<"
            self.__emitCurrentToken()
            self.__currentToken = cast(HTMLCommentOrCharacter, self.__createNewToken(HTMLToken.TokenType.Character))
            self.__currentToken.data = "/"
            self.__emitCurrentToken()

            for char in self.__temporaryBuffer:
                self.__currentToken = cast(HTMLCommentOrCharacter,
                                           self.__createNewToken(HTMLToken.TokenType.Character))
                self.__currentToken.data = char
                self.__emitCurrentToken()
            self.__reconsumeIn(self.State.RAWTEXT)

        if charIsWhitespace(self.__currentInputChar):
            if self.__currentToken.name == self.__lastEmittedStartTagName:
                self.switchStateTo(self.State.BeforeAttributeName)
            else:
                elseCase()
        elif self.__currentInputChar == "/":
            if self.__currentToken.name == self.__lastEmittedStartTagName:
                self.switchStateTo(self.State.SelfClosingStartTag)
            else:
                elseCase()
        elif self.__currentInputChar == ">":
            if self.__currentToken.name == self.__lastEmittedStartTagName:
                self.switchStateTo(self.State.Data)
                self.__emitCurrentToken()
            else:
                elseCase()
        elif charIsUppercaseAlpha(self.__currentInputChar):
            self.__currentToken.appendCharToTokenName(self.__currentInputChar.lower())
            self.__temporaryBuffer.append(self.__currentInputChar)
        elif charIsLowercaseAlpha(self.__currentInputChar):
            self.__currentToken.appendCharToTokenName(self.__currentInputChar)
            self.__temporaryBuffer.append(self.__currentInputChar)
        else:
            elseCase()

    def handleScriptDataLessThanSign(self) -> None:
        if self.__currentInputChar == "/":
            self.__temporaryBuffer = []
            self.switchStateTo(self.State.ScriptDataEndTagOpen)
        elif self.__currentInputChar == "!":
            self.switchStateTo(self.State.ScriptDataEscapeStart)
            self.__currentToken = cast(HTMLCommentOrCharacter, self.__createNewToken(HTMLToken.TokenType.Character))
            self.__currentToken.data = "<"
            self.__emitCurrentToken()
            self.__currentToken = cast(HTMLCommentOrCharacter, self.__createNewToken(HTMLToken.TokenType.Character))
            self.__currentToken.data = "!"
            self.__emitCurrentToken()
        else:
            self.__currentToken = cast(HTMLCommentOrCharacter, self.__createNewToken(HTMLToken.TokenType.Character))
            self.__currentToken.data = "<"
            self.__emitCurrentToken()
            self.__reconsumeIn(self.State.ScriptData)

    def handleScriptDataEndTagOpen(self) -> None:
        if charIsUppercaseAlpha(self.__currentInputChar) or charIsLowercaseAlpha(self.__currentInputChar):
            self.__currentToken = cast(HTMLTag, self.__createNewToken(HTMLToken.TokenType.EndTag))
            self.__currentToken.name = ""
            self.__reconsumeIn(self.State.ScriptDataEndTagName)
        else:
            self.__currentToken = cast(HTMLCommentOrCharacter, self.__createNewToken(HTMLToken.TokenType.Character))
            self.__currentToken.data = "<"
            self.__emitCurrentToken()
            self.__currentToken = cast(HTMLCommentOrCharacter, self.__createNewToken(HTMLToken.TokenType.Character))
            self.__currentToken.data = "/"
            self.__emitCurrentToken()
            self.__reconsumeIn(self.State.ScriptData)

    def handleScriptDataEndTagName(self) -> None:
        self.__currentToken = cast(HTMLTag, self.__currentToken)

        def elseCase() -> None:
            self.__currentToken = cast(HTMLCommentOrCharacter, self.__createNewToken(HTMLToken.TokenType.Character))
            self.__currentToken.data = "<"
            self.__emitCurrentToken()
            self.__currentToken = cast(HTMLCommentOrCharacter, self.__createNewToken(HTMLToken.TokenType.Character))
            self.__currentToken.data = "/"
            self.__emitCurrentToken()
            for char in self.__temporaryBuffer:
                self.__currentToken = cast(HTMLCommentOrCharacter,
                                           self.__createNewToken(HTMLToken.TokenType.Character))
                self.__currentToken.data = char
                self.__emitCurrentToken()
            self.__reconsumeIn(self.State.ScriptData)

        if charIsWhitespace(self.__currentInputChar):
            if self.__currentToken.name == self.__lastEmittedStartTagName:
                self.switchStateTo(self.State.BeforeAttributeName)
            else:
                elseCase()
        elif self.__currentInputChar == "/":
            if self.__currentToken.name == self.__lastEmittedStartTagName:
                self.switchStateTo(self.State.SelfClosingStartTag)
            else:
                elseCase()
        elif self.__currentInputChar == ">":
            if self.__currentToken.name == self.__lastEmittedStartTagName:
                self.switchStateTo(self.State.Data)
                self.__emitCurrentToken()
            else:
                elseCase()
        elif charIsUppercaseAlpha(self.__currentInputChar):
            self.__currentToken.appendCharToTokenName(self.__currentInputChar.lower())
            self.__temporaryBuffer.append(self.__currentInputChar)
        elif charIsLowercaseAlpha(self.__currentInputChar):
            self.__currentToken.appendCharToTokenName(self.__currentInputChar)
            self.__temporaryBuffer.append(self.__currentInputChar)
        else:
            elseCase()

    def handleScriptDataEscapeStart(self) -> None:
        raise NotImplementedError

    def handleScriptDataEscapeStartDash(self) -> None:
        raise NotImplementedError

    def handleScriptDataEscaped(self) -> None:
        raise NotImplementedError

    def handleScriptDataEscapedDash(self) -> None:
        raise NotImplementedError

    def handleScriptDataEscapedDashDash(self) -> None:
        raise NotImplementedError

    def handleScriptDataEscapedLessThanSign(self) -> None:
        raise NotImplementedError

    def handleScriptDataEscapedEndTagOpen(self) -> None:
        raise NotImplementedError

    def handleScriptDataEscapedEndTagName(self) -> None:
        raise NotImplementedError

    def handleScriptDataDoubleEscapeStart(self) -> None:
        raise NotImplementedError

    def handleScriptDataDoubleEscaped(self) -> None:
        raise NotImplementedError

    def handleScriptDataDoubleEscapedDash(self) -> None:
        raise NotImplementedError

    def handleScriptDataDoubleEscapedDashDash(self) -> None:
        raise NotImplementedError

    def handleScriptDataDoubleEscapedLessThanSign(self) -> None:
        raise NotImplementedError

    def handleScriptDataDoubleEscapeEnd(self) -> None:
        raise NotImplementedError

    def handleBeforeAttributeName(self) -> None:
        self.__currentToken = cast(HTMLTag, self.__currentToken)

        if self.__currentInputChar is None:
            self.__reconsumeIn(self.State.AfterAttributeName)
        elif charIsWhitespace(self.__currentInputChar):
            self.__continueIn(self.State.BeforeAttributeName)
        else:
            self.__currentToken.createNewAttribute()
            self.__reconsumeIn(self.State.AttributeName)

    def handleAttributeName(self) -> None:
        self.__currentToken = cast(HTMLTag, self.__currentToken)

        if (
                self.__currentInputChar is None
                or charIsWhitespace(self.__currentInputChar)
                or self.__currentInputChar == "/"
                or self.__currentInputChar == ">"
        ):
            self.__reconsumeIn(self.State.AfterAttributeName)
        elif self.__currentInputChar == "=":
            self.switchStateTo(self.State.BeforeAttributeValue)
        elif self.__currentInputChar.isupper() and self.__currentInputChar.isalpha():
            self.__currentToken.addCharToAttributeName(self.__currentInputChar.lower())
        else:
            self.__currentToken.addCharToAttributeName(self.__currentInputChar)
            self.__continueIn(self.State.AttributeName)

    def handleAfterAttributeName(self) -> None:
        self.__currentToken = cast(HTMLTag, self.__currentToken)

        if charIsWhitespace(self.__currentInputChar):
            pass
        elif self.__currentInputChar == "/":
            self.switchStateTo(self.State.SelfClosingStartTag)
        elif self.__currentInputChar == "=":
            self.switchStateTo(self.State.BeforeAttributeValue)
        elif self.__currentInputChar == ">":
            self.switchStateTo(self.State.Data)
            self.__emitCurrentToken()
        elif self.__currentInputChar is None:
            raise NotImplementedError
        else:
            self.__currentToken.createNewAttribute()
            self.__reconsumeIn(self.State.AttributeName)

    def handleBeforeAttributeValue(self) -> None:
        if charIsWhitespace(self.__currentInputChar):
            self.__continueIn(self.State.BeforeAttributeValue)
        elif self.__currentInputChar == '"':
            self.switchStateTo(self.State.AttributeValueDoubleQuoted)
        elif self.__currentInputChar == "'":
            self.switchStateTo(self.State.AttributeValueSingleQuoted)
        elif self.__currentInputChar == ">":
            self.switchStateTo(self.State.Data)
            self.__emitCurrentToken()
        else:
            self.__reconsumeIn(self.State.AttributeValueUnquoted)

    def handleAttributeValueDoubleQuoted(self) -> None:
        self.__currentToken = cast(HTMLTag, self.__currentToken)
        if self.__currentInputChar is None:
            self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
            self.__emitCurrentToken()
        elif self.__currentInputChar == '"':
            self.switchStateTo(self.State.AfterAttributeValueQuoted)
        elif self.__currentInputChar == "&":
            self.__returnState = self.State.AttributeValueDoubleQuoted
            self.switchStateTo(self.State.CharacterReference)
        else:
            self.__currentToken.addCharToAttributeValue(self.__currentInputChar)
            self.__continueIn(self.State.AttributeValueDoubleQuoted)

    def handleAttributeValueSingleQuoted(self) -> None:
        self.__currentToken = cast(HTMLTag, self.__currentToken)
        if self.__currentInputChar is None:
            self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
            self.__emitCurrentToken()
        elif self.__currentInputChar == "'":
            self.switchStateTo(self.State.AfterAttributeValueQuoted)
        elif self.__currentInputChar == "&":
            self.__returnState = self.State.AttributeValueSingleQuoted
            self.switchStateTo(self.State.CharacterReference)
        else:
            self.__currentToken.addCharToAttributeValue(self.__currentInputChar)
            self.__continueIn(self.State.AttributeValueSingleQuoted)

    def handleAttributeValueUnquoted(self) -> None:
        self.__currentToken = cast(HTMLTag, self.__currentToken)
        if self.__currentInputChar is None:
            self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
            self.__emitCurrentToken()
        elif charIsWhitespace(self.__currentInputChar):
            self.switchStateTo(self.State.BeforeAttributeName)
        elif self.__currentInputChar == "&":
            self.__returnState = self.State.AttributeValueUnquoted
            self.switchStateTo(self.State.CharacterReference)
        elif self.__currentInputChar == ">":
            self.switchStateTo(self.State.Data)
            self.__emitCurrentToken()
        else:
            self.__currentToken.addCharToAttributeValue(self.__currentInputChar)
            self.__continueIn(self.State.AttributeValueUnquoted)

    def handleAfterAttributeValueQuoted(self) -> None:
        if self.__currentInputChar is None:
            self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
            self.__emitCurrentToken()
        elif charIsWhitespace(self.__currentInputChar):
            self.switchStateTo(self.State.BeforeAttributeName)
        elif self.__currentInputChar == "/":
            self.switchStateTo(self.State.SelfClosingStartTag)
        elif self.__currentInputChar == ">":
            self.switchStateTo(self.State.Data)
            self.__emitCurrentToken()
        else:
            self.__reconsumeIn(self.State.BeforeAttributeName)

    def handleSelfClosingStartTag(self) -> None:
        self.__currentToken = cast(HTMLTag, self.__currentToken)
        if self.__currentInputChar == ">":
            self.__currentToken.selfClosing = True
            self.switchStateTo(self.State.Data)
            self.__emitCurrentToken()
        elif self.__currentInputChar is None:
            self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
            self.__emitCurrentToken()
        else:
            self.__reconsumeIn(self.State.BeforeAttributeName)

    def handleBogusComment(self) -> None:
        raise NotImplementedError

    def handleMarkupDeclarationOpen(self) -> None:
        if self.__nextCharactersAre("--"):
            self.__consumeCharacters("--")
            self.__currentToken = self.__createNewToken(HTMLToken.TokenType.Comment)
            self.switchStateTo(self.State.CommentStart)
        elif self.__nextCharactersAre("DOCTYPE"):
            self.__consumeCharacters("DOCTYPE")
            self.switchStateTo(self.State.DOCTYPE)

    def handleCommentStart(self) -> None:

        if self.__currentInputChar == "-":
            self.switchStateTo(self.State.CommentStartDash)
        elif self.__currentInputChar == ">":
            self.switchStateTo(self.State.Data)
            self.__emitCurrentToken()
        else:
            self.__reconsumeIn(self.State.Comment)

    def handleCommentStartDash(self) -> None:
        self.__currentToken = cast(HTMLCommentOrCharacter, self.__currentToken)
        if self.__currentInputChar == "-":
            self.switchStateTo(self.State.CommentEnd)
        elif self.__currentInputChar == ">":
            self.switchStateTo(self.State.Data)
            self.__emitCurrentToken()
        elif self.__currentInputChar is None:
            self.__emitCurrentToken()
            self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
            self.__emitCurrentToken()
        else:
            if self.__currentToken.data is not None:
                self.__currentToken.data += "-"
            else:
                self.__currentToken.data = "-"
            self.__reconsumeIn(self.State.Comment)

    def handleComment(self) -> None:
        self.__currentToken = cast(HTMLCommentOrCharacter, self.__currentToken)
        if self.__currentInputChar == "-":
            self.switchStateTo(self.State.CommentEndDash)
        elif self.__currentInputChar is None:
            self.__emitCurrentToken()
            self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
            self.__emitCurrentToken()
        else:
            if self.__currentToken.data is not None:
                self.__currentToken.data += self.__currentInputChar
            else:
                self.__currentToken.data = self.__currentInputChar
            self.__continueIn(self.State.Comment)

    def handleCommentLessThanSign(self) -> None:
        raise NotImplementedError

    def handleCommentLessThanSignBang(self) -> None:
        raise NotImplementedError

    def handleCommentLessThanSignBangDash(self) -> None:
        raise NotImplementedError

    def handleCommentLessThanSignBangDashDash(self) -> None:
        raise NotImplementedError

    def handleCommentEndDash(self) -> None:
        self.__currentToken = cast(HTMLCommentOrCharacter, self.__currentToken)
        if self.__currentInputChar == "-":
            self.switchStateTo(self.State.CommentEnd)
        elif self.__currentInputChar is None:
            self.__emitCurrentToken()
            self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
            self.__emitCurrentToken()
        else:
            if self.__currentToken.data is not None:
                self.__currentToken.data += "-"
            else:
                self.__currentToken.data = "-"
            self.__reconsumeIn(self.State.Comment)

    def handleCommentEnd(self) -> None:
        self.__currentToken = cast(HTMLCommentOrCharacter, self.__currentToken)
        if self.__currentInputChar == ">":
            self.switchStateTo(self.State.Data)
            self.__emitCurrentToken()
        elif self.__currentInputChar == "-":
            if self.__currentToken.data is not None:
                self.__currentToken.data += "-"
            else:
                self.__currentToken.data = "-"
            self.__continueIn(self.State.CommentEnd)
        elif self.__currentInputChar is None:
            self.__emitCurrentToken()
            self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
            self.__emitCurrentToken()
        else:
            if self.__currentToken.data is not None:
                self.__currentToken.data += "-"
            else:
                self.__currentToken.data = "-"
            self.__reconsumeIn(self.State.Comment)

    def handleCommentEndBang(self) -> None:
        raise NotImplementedError

    def handleDOCTYPE(self) -> None:
        if charIsWhitespace(self.__currentInputChar):
            self.switchStateTo(self.State.BeforeDOCTYPEName)

    def handleBeforeDOCTYPEName(self) -> None:
        if charIsWhitespace(self.__currentInputChar):
            self.__ignoreCharacterAndContinueTo(self.State.BeforeDOCTYPEName)
        else:
            self.__currentToken = cast(HTMLDoctype, self.__createNewToken(HTMLToken.TokenType.DOCTYPE))
            if self.__currentToken.name is not None and self.__currentInputChar is not None:
                self.__currentToken.name += self.__currentInputChar
            else:
                self.__currentToken.name = self.__currentInputChar

            self.switchStateTo(self.State.DOCTYPEName)

    def handleDOCTYPEName(self) -> None:
        self.__currentToken = cast(HTMLDoctype, self.__currentToken)
        if self.__currentInputChar == ">":
            self.switchStateTo(self.State.Data)
            self.__emitCurrentToken()
        else:
            self.__currentToken.name = self.__currentToken.name + str(self.__currentInputChar)\
                                        if self.__currentToken.name else str(self.__currentInputChar)
            self.__continueIn(self.State.DOCTYPEName)

    def handleAfterDOCTYPEName(self) -> None:
        raise NotImplementedError

    def handleAfterDOCTYPEPublicKeyword(self) -> None:
        raise NotImplementedError

    def handleBeforeDOCTYPEPublicIdentifier(self) -> None:
        raise NotImplementedError

    def handleDOCTYPEPublicIdentifierDoubleQuoted(self) -> None:
        raise NotImplementedError

    def handleDOCTYPEPublicIdentifierSingleQuoted(self) -> None:
        raise NotImplementedError

    def handleAfterDOCTYPEPublicIdentifier(self) -> None:
        raise NotImplementedError

    def handleBetweenDOCTYPEPublicAndSystemIdentifiers(self) -> None:
        raise NotImplementedError

    def handleAfterDOCTYPESystemKeyword(self) -> None:
        raise NotImplementedError

    def handleBeforeDOCTYPESystemIdentifier(self) -> None:
        raise NotImplementedError

    def handleDOCTYPESystemIdentifierDoubleQuoted(self) -> None:
        raise NotImplementedError

    def handleDOCTYPESystemIdentifierSingleQuoted(self) -> None:
        raise NotImplementedError

    def handleAfterDOCTYPESystemIdentifier(self) -> None:
        raise NotImplementedError

    def handleBogusDOCTYPE(self) -> None:
        raise NotImplementedError

    def handleCDATASection(self) -> None:
        raise NotImplementedError

    def handleCDATASectionBracket(self) -> None:
        raise NotImplementedError

    def handleCDATASectionEnd(self) -> None:
        raise NotImplementedError

    def handleCharacterReference(self) -> None:
        self.__temporaryBuffer.append("&")
        self.__returnState = cast(HTMLTokenizer.State, self.__returnState)
        if self.__currentInputChar.isalnum():
            self.__reconsumeIn(self.State.NamedCharacterReference)
        elif self.__currentInputChar == "#":
            self.__temporaryBuffer.append(self.__currentInputChar)
            self.switchStateTo(self.State.NumericCharacterReference)
        else:
            self.__flushTemporaryBuffer()
            self.__reconsumeIn(self.__returnState)

    def handleNamedCharacterReference(self) -> None:
        self.__returnState = cast(HTMLTokenizer.State, self.__returnState)
        consumedCharacters: List[str] = [self.__currentInputChar]
        while atLeastOneNameStartsWith("".join(consumedCharacters)):
            nextChar = self.__nextCodePoint()
            if nextChar is not None:
                self.__currentInputChar = nextChar
                consumedCharacters.append(nextChar)
                if nextChar == ";":
                    break
        match = getNamedCharFromTable("".join(consumedCharacters))
        if match is not None:
            # TODO: Implement case.
            if self.__currentToken is not None:
                self.__currentToken = cast(HTMLTag, self.__currentToken)
                for match_item in match:
                    self.__currentToken.addCharToAttributeValue(chr(match_item))
            else:
                self.__currentToken = cast(HTMLCommentOrCharacter,
                                           self.__createNewToken(HTMLToken.TokenType.Character))
                for match_item in match:
                    self.__currentToken.data = self.__currentToken.data + chr(match_item)\
                                                if self.__currentToken.data is not None else chr(match_item)
                self.__emitCurrentToken()
            self.switchStateTo(self.__returnState)
        else:
            self.__temporaryBuffer.extend(consumedCharacters)
            self.__flushTemporaryBuffer()
            self.__reconsumeIn(self.State.AmbiguousAmpersand)

    def handleAmbiguousAmpersand(self) -> None:
        self.__returnState = cast(HTMLTokenizer.State, self.__returnState)
        if self.__currentInputChar.isalnum():
            self.__temporaryBuffer.append(self.__currentInputChar)
            self.__flushTemporaryBuffer()
        elif self.__currentInputChar == ";":
            self.__reconsumeIn(self.__returnState)
        else:
            self.__reconsumeIn(self.__returnState)

    def handleNumericCharacterReference(self) -> None:
        if self.__currentInputChar == "X" or self.__currentInputChar == "x":
            self.__temporaryBuffer.append(self.__currentInputChar)
            self.switchStateTo(self.State.HexadecimalCharacterReferenceStart)
        else:
            self.__reconsumeIn(self.State.DecimalCharacterReferenceStart)

    def handleHexadecimalCharacterReferenceStart(self) -> None:
        raise NotImplementedError

    def handleDecimalCharacterReferenceStart(self) -> None:
        if self.__currentInputChar.isdigit():
            self.__reconsumeIn(self.State.HexadecimalCharacterReference)
        else:
            # TODO: handle parse error.
            self.__flushTemporaryBuffer()
            if self.__returnState is not None:
                self.__reconsumeIn(self.__returnState)

    def handleHexadecimalCharacterReference(self) -> None:
        if self.__currentInputChar.isdigit():
            self.__characterReferenceCode *= 16
            self.__characterReferenceCode += ord(self.__currentInputChar) - 0x0030
        elif charIsUppercaseAlpha(self.__currentInputChar):
            self.__characterReferenceCode *= 16
            self.__characterReferenceCode += ord(self.__currentInputChar) - 0x0037
        elif charIsLowercaseAlpha(self.__currentInputChar):
            self.__characterReferenceCode *= 16
            self.__characterReferenceCode += ord(self.__currentInputChar) - 0x0057
        elif self.__currentInputChar == ";":
            self.switchStateTo(self.State.NumericCharacterReferenceEnd)
        else:
            # TODO: Handle parse error.
            self.__reconsumeIn(self.State.NumericCharacterReferenceEnd)

    def handleDecimalCharacterReference(self) -> None:
        raise NotImplementedError

    def handleNumericCharacterReferenceEnd(self) -> None:
        if self.__characterReferenceCode == 0:
            # TODO: handle parse error.
            self.__characterReferenceCode = 0xFFFD
        elif self.__characterReferenceCode > 0x10ffff:
            # TODO: handle parse error.
            self.__characterReferenceCode = 0xFFFD
        elif charIsSurrogate(self.__characterReferenceCode):
            # TODO: handle parse error.
            self.__characterReferenceCode = 0xFFFD
        elif charIsNoncharacter(self.__characterReferenceCode):
            # TODO: Handle parse error.
            pass
        elif self.__characterReferenceCode == 0x0D or (
                charIsControl(self.__characterReferenceCode) and not
                charIsWhitespace(chr(self.__characterReferenceCode))):

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
            value = conversionTable.get(self.__characterReferenceCode, None)
            if value is not None:
                self.__characterReferenceCode = value

        self.__temporaryBuffer = []
        self.__temporaryBuffer.append(chr(self.__characterReferenceCode))
        self.__flushTemporaryBuffer()
        if self.__returnState is not None:
            self.switchStateTo(self.__returnState)

    def __getStateSwitcher(self) -> Union[Callable[[], None], None]:

        switcher = {
            self.State.Data: self.handleData,
            self.State.RCDATA: self.handleRCDATA,
            self.State.RAWTEXT: self.handleRAWTEXT,
            self.State.ScriptData: self.handleScriptData,
            self.State.PLAINTEXT: self.handlePLAINTEXT,
            self.State.TagOpen: self.handleTagOpen,
            self.State.EndTagOpen: self.handleEndTagOpen,
            self.State.TagName: self.handleTagName,
            self.State.RCDATALessThanSign: self.handleRCDATALessThanSign,
            self.State.RCDATAEndTagOpen: self.handleRCDATAEndTagOpen,
            self.State.RCDATAEndTagName: self.handleRCDATAEndTagName,
            self.State.RAWTEXTLessThanSign: self.handleRAWTEXTLessThanSign,
            self.State.RAWTEXTEndTagOpen: self.handleRAWTEXTEndTagOpen,
            self.State.RAWTEXTEndTagName: self.handleRAWTEXTEndTagName,
            self.State.ScriptDataLessThanSign: self.handleScriptDataLessThanSign,
            self.State.ScriptDataEndTagOpen: self.handleScriptDataEndTagOpen,
            self.State.ScriptDataEndTagName: self.handleScriptDataEndTagName,
            self.State.ScriptDataEscapeStart: self.handleScriptDataEscapeStart,
            self.State.ScriptDataEscapeStartDash: self.handleScriptDataEscapeStartDash,
            self.State.ScriptDataEscaped: self.handleScriptDataEscaped,
            self.State.ScriptDataEscapedDash: self.handleScriptDataEscapedDash,
            self.State.ScriptDataEscapedDashDash: self.handleScriptDataEscapedDashDash,
            self.State.ScriptDataEscapedLessThanSign: self.handleScriptDataEscapedLessThanSign,
            self.State.ScriptDataEscapedEndTagOpen: self.handleScriptDataEscapedEndTagOpen,
            self.State.ScriptDataEscapedEndTagName: self.handleScriptDataEscapedEndTagName,
            self.State.ScriptDataDoubleEscapeStart: self.handleScriptDataDoubleEscapeStart,
            self.State.ScriptDataDoubleEscaped: self.handleScriptDataDoubleEscaped,
            self.State.ScriptDataDoubleEscapedDash: self.handleScriptDataDoubleEscapedDash,
            self.State.ScriptDataDoubleEscapedDashDash: self.handleScriptDataDoubleEscapedDashDash,
            self.State.ScriptDataDoubleEscapedLessThanSign: self.handleScriptDataDoubleEscapedLessThanSign,
            self.State.ScriptDataDoubleEscapeEnd: self.handleScriptDataDoubleEscapeEnd,
            self.State.BeforeAttributeName: self.handleBeforeAttributeName,
            self.State.AttributeName: self.handleAttributeName,
            self.State.AfterAttributeName: self.handleAfterAttributeName,
            self.State.BeforeAttributeValue: self.handleBeforeAttributeValue,
            self.State.AttributeValueDoubleQuoted: self.handleAttributeValueDoubleQuoted,
            self.State.AttributeValueSingleQuoted: self.handleAttributeValueSingleQuoted,
            self.State.AttributeValueUnquoted: self.handleAttributeValueUnquoted,
            self.State.AfterAttributeValueQuoted: self.handleAfterAttributeValueQuoted,
            self.State.SelfClosingStartTag: self.handleSelfClosingStartTag,
            self.State.BogusComment: self.handleBogusComment,
            self.State.MarkupDeclarationOpen: self.handleMarkupDeclarationOpen,
            self.State.CommentStart: self.handleCommentStart,
            self.State.CommentStartDash: self.handleCommentStartDash,
            self.State.Comment: self.handleComment,
            self.State.CommentLessThanSign: self.handleCommentLessThanSign,
            self.State.CommentLessThanSignBang: self.handleCommentLessThanSignBang,
            self.State.CommentLessThanSignBangDash: self.handleCommentLessThanSignBangDash,
            self.State.CommentLessThanSignBangDashDash: self.handleCommentLessThanSignBangDashDash,
            self.State.CommentEndDash: self.handleCommentEndDash,
            self.State.CommentEnd: self.handleCommentEnd,
            self.State.CommentEndBang: self.handleCommentEndBang,
            self.State.DOCTYPE: self.handleDOCTYPE,
            self.State.BeforeDOCTYPEName: self.handleBeforeDOCTYPEName,
            self.State.DOCTYPEName: self.handleDOCTYPEName,
            self.State.AfterDOCTYPEName: self.handleAfterDOCTYPEName,
            self.State.AfterDOCTYPEPublicKeyword: self.handleAfterDOCTYPEPublicKeyword,
            self.State.BeforeDOCTYPEPublicIdentifier: self.handleBeforeDOCTYPEPublicIdentifier,
            self.State.DOCTYPEPublicIdentifierDoubleQuoted: self.handleDOCTYPEPublicIdentifierDoubleQuoted,
            self.State.DOCTYPEPublicIdentifierSingleQuoted: self.handleDOCTYPEPublicIdentifierSingleQuoted,
            self.State.AfterDOCTYPEPublicIdentifier: self.handleAfterDOCTYPEPublicIdentifier,
            self.State.BetweenDOCTYPEPublicAndSystemIdentifiers: self.handleBetweenDOCTYPEPublicAndSystemIdentifiers,
            self.State.AfterDOCTYPESystemKeyword: self.handleAfterDOCTYPESystemKeyword,
            self.State.BeforeDOCTYPESystemIdentifier: self.handleBeforeDOCTYPESystemIdentifier,
            self.State.DOCTYPESystemIdentifierDoubleQuoted: self.handleDOCTYPESystemIdentifierDoubleQuoted,
            self.State.DOCTYPESystemIdentifierSingleQuoted: self.handleDOCTYPESystemIdentifierSingleQuoted,
            self.State.AfterDOCTYPESystemIdentifier: self.handleAfterDOCTYPESystemIdentifier,
            self.State.BogusDOCTYPE: self.handleBogusDOCTYPE,
            self.State.CDATASection: self.handleCDATASection,
            self.State.CDATASectionBracket: self.handleCDATASectionBracket,
            self.State.CDATASectionEnd: self.handleCDATASectionEnd,
            self.State.CharacterReference: self.handleCharacterReference,
            self.State.NamedCharacterReference: self.handleNamedCharacterReference,
            self.State.AmbiguousAmpersand: self.handleAmbiguousAmpersand,
            self.State.NumericCharacterReference: self.handleNumericCharacterReference,
            self.State.HexadecimalCharacterReferenceStart: self.handleHexadecimalCharacterReferenceStart,
            self.State.DecimalCharacterReferenceStart: self.handleDecimalCharacterReferenceStart,
            self.State.HexadecimalCharacterReference: self.handleHexadecimalCharacterReference,
            self.State.DecimalCharacterReference: self.handleDecimalCharacterReference,
            self.State.NumericCharacterReferenceEnd: self.handleNumericCharacterReferenceEnd,
        }

        return switcher.get(self.state, None)

    def run(self) -> None:
        while self.__cursor < len(self.__html):
            tokenPoint = self.__nextCodePoint()
            if tokenPoint is None:
                self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
                self.__emitCurrentToken()
            self.__currentInputChar = cast(str, tokenPoint)
            switcher = self.__getStateSwitcher()
            if switcher is not None:
                switcher()

        self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
        self.__emitCurrentToken()

