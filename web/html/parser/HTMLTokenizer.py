from enum import Enum, auto
from typing import Union, Callable, Any, cast, List
from .HTMLToken import HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter
from .utils import charIsAlpha, charIsControl, charIsNoncharacter, charIsWhitespace, charIsUppercaseAlpha, \
    charIsLowercaseAlpha, charIsSurrogate
from .Entities import getNamedCharFromTable, atLeastOneNameStartsWith


class HTMLTokenizer:
    def _emitCurrentToken(self) -> None:
        self._tokenHandlerCb(self._currentToken)
        if self._currentToken.type == HTMLToken.TokenType.StartTag:
            self._lastEmittedStartTagName = self._currentToken.name
        self._currentToken = None
        print("Current state: ", self.state)

    def _createNewToken(
            self, tokenType: HTMLToken.TokenType
    ) -> Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]:
        token = None
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

    def _continueIn(self, state: State) -> None:
        self.switchStateTo(state)

    def _ignoreCharacterAndContinueTo(self, newState: State) -> None:
        self.switchStateTo(newState)

    def switchStateTo(self, newState: State) -> None:
        """
        Switch state and consume next character.
        """
        self.state = newState

    def _reconsumeIn(self, newState: State) -> None:
        """
        Switch state without consuming next character.
        """
        self.state = newState
        switcher = self._getStateSwitcher()
        if switcher is not None:
            switcher()

    def _nextCharactersAre(self, characters: str) -> bool:
        for index in range(len(characters)):
            if self._cursor >= len(self._html):
                return False
            char = self._html[self._cursor + index]
            if char.lower() != characters[index].lower():
                return False

        return True

    def _consumeCharacters(self, characters: str) -> None:
        self._cursor += len(characters)

    def _nextCodePoint(self) -> Union[str, None]:
        if self._cursor >= len(self._html):
            return
        char = self._html[self._cursor]
        self._cursor += 1
        return char

    def __init__(self, html: str, tokenHandlerCb: Callable):
        self.state = self.State.Data
        self._html = html
        self._cursor = 0
        self._currentInputChar: Union[str, None] = None
        self._returnState: Union[Any, None] = None
        self._currentToken: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter, None] = None
        self._tokenHandlerCb = tokenHandlerCb
        self._temporaryBuffer: List[str] = []
        self._characterReferenceCode: int = 0
        self._lastEmittedStartTagName: str = None

    def _flushTemporaryBuffer(self) -> None:
        if self._currentToken is not None:
            self._currentToken.addCharToAttributeValue("".join(self._temporaryBuffer))
        else:
            for char in self._temporaryBuffer:
                self._currentToken = cast(HTMLCommentOrCharacter, self._createNewToken(HTMLToken.TokenType.Character))
                self._currentToken.data = char
                self._emitCurrentToken()
        self._temporaryBuffer = []

    def _getStateSwitcher(self) -> Union[Callable[[], None], None]:
        def handleData() -> None:
            if self._currentInputChar == "&":
                self._returnState = self.State.Data
                self.switchStateTo(self.State.CharacterReference)
            elif self._currentInputChar == "<":
                self.switchStateTo(self.State.TagOpen)
            elif self._currentInputChar is None:
                self._currentToken = self._createNewToken(HTMLToken.TokenType.EOF)
                self._emitCurrentToken()
            else:
                self._currentToken = cast(HTMLCommentOrCharacter, self._createNewToken(HTMLToken.TokenType.Character))
                self._currentToken.data = self._currentInputChar
                self._continueIn(self.State.Data)
                self._emitCurrentToken()

        def handleRCDATA() -> None:
            if self._currentInputChar == "&":
                self._returnState = self.State.RCDATA
                self.switchStateTo(self.State.CharacterReference)
            elif self._currentInputChar == "<":
                self.switchStateTo(self.State.RCDATALessThanSign)
            elif self._currentInputChar is None:
                self._currentToken = self._createNewToken(HTMLToken.TokenType.EOF)
                self._emitCurrentToken()
            else:
                self._currentToken = cast(HTMLCommentOrCharacter, self._createNewToken(HTMLToken.TokenType.Character))
                self._currentToken.data = self._currentInputChar
                self._emitCurrentToken()

        def handleRAWTEXT() -> None:
            if self._currentInputChar == "<":
                self.switchStateTo(self.State.RAWTEXTLessThanSign)
            elif self._currentInputChar is None:
                self._currentToken = self._createNewToken(HTMLToken.TokenType.EOF)
                self._emitCurrentToken()
            else:
                self._currentToken = cast(HTMLCommentOrCharacter, self._createNewToken(HTMLToken.TokenType.Character))
                self._currentToken.data = self._currentInputChar
                self._emitCurrentToken()

        def handleScriptData() -> None:
            if self._currentInputChar == "<":
                self.switchStateTo(self.State.ScriptDataLessThanSign)
            elif self._currentInputChar is None:
                self._currentToken = self._createNewToken(HTMLToken.TokenType.EOF)
                self._emitCurrentToken()
            else:
                self._currentToken = cast(HTMLCommentOrCharacter, self._createNewToken(HTMLToken.TokenType.Character))
                self._currentToken.data = self._currentInputChar
                self._emitCurrentToken()

        def handlePLAINTEXT() -> None:
            raise NotImplementedError

        def handleTagOpen() -> None:
            if self._currentInputChar == "!":
                self._reconsumeIn(self.State.MarkupDeclarationOpen)
            elif self._currentInputChar == "/":
                self.switchStateTo(self.State.EndTagOpen)
            elif self._currentInputChar.isalpha():
                self._currentToken = cast(HTMLTag, self._createNewToken(HTMLToken.TokenType.StartTag))
                self._reconsumeIn(self.State.TagName)

        def handleEndTagOpen() -> None:
            self._currentToken = self._createNewToken(HTMLToken.TokenType.EndTag)
            self._reconsumeIn(self.State.TagName)

        def handleTagName() -> None:
            if self._currentInputChar is None:
                self._currentToken = self._createNewToken(HTMLToken.TokenType.EOF)
                self._emitCurrentToken()
            elif charIsWhitespace(self._currentInputChar):
                self.switchStateTo(self.State.BeforeAttributeName)
            elif self._currentInputChar == ">":
                self.switchStateTo(self.State.Data)
                self._emitCurrentToken()
            else:
                self._currentToken = cast(HTMLTag, self._currentToken)
                if self._currentToken.name is not None and self._currentInputChar is not None:
                    self._currentToken.name += self._currentInputChar
                else:
                    self._currentToken.name = self._currentInputChar
                self._continueIn(self.State.TagName)

        def handleRCDATALessThanSign() -> None:
            if self._currentInputChar == "/":
                self._temporaryBuffer = []
                self.switchStateTo(self.State.RCDATAEndTagOpen)
            else:
                self._currentToken = cast(HTMLCommentOrCharacter, self._createNewToken(HTMLToken.TokenType.Character))
                self._currentToken.data = "<"
                self._emitCurrentToken()
                self._reconsumeIn(self.State.RCDATA)

        def handleRCDATAEndTagOpen() -> None:
            if charIsAlpha(self._currentInputChar):
                self._currentToken = self._createNewToken(HTMLToken.TokenType.EndTag)
                self._currentToken.name = ""
                self._reconsumeIn(self.State.RCDATAEndTagName)
            else:
                self._currentToken = cast(HTMLCommentOrCharacter, self._createNewToken(HTMLToken.TokenType.Character))
                self._currentToken.data = "<"
                self._emitCurrentToken()
                self._currentToken = cast(HTMLCommentOrCharacter, self._createNewToken(HTMLToken.TokenType.Character))
                self._currentToken.data = "/"
                self._emitCurrentToken()
                self._reconsumeIn(self.State.RCDATA)

        def handleRCDATAEndTagName() -> None:
            print("Current char:", self._currentInputChar)
            print("Current token:", self._currentToken)
            print("Last emited token:", self._lastEmittedStartTagName)

            def elseCase():
                self._currentToken = cast(HTMLCommentOrCharacter, self._createNewToken(HTMLToken.TokenType.Character))
                self._currentToken.data = "<"
                self._emitCurrentToken()
                self._currentToken = cast(HTMLCommentOrCharacter, self._createNewToken(HTMLToken.TokenType.Character))
                self._currentToken.data = "/"
                self._emitCurrentToken()

                for char in self._temporaryBuffer:
                    self._currentToken = cast(HTMLCommentOrCharacter,
                                              self._createNewToken(HTMLToken.TokenType.Character))
                    self._currentToken.data = char
                    self._emitCurrentToken()
                self._reconsumeIn(self.State.RCDATA)

            if charIsWhitespace(self._currentInputChar):
                if self._currentToken.name == self._lastEmittedStartTagName:
                    self.switchStateTo(self.State.BeforeAttributeName)
                else:
                    elseCase()
            elif self._currentInputChar == "/":
                if self._currentToken.name == self._lastEmittedStartTagName:
                    self.switchStateTo(self.State.SelfClosingStartTag)
                else:
                    elseCase()
            elif self._currentInputChar == ">":
                if self._currentToken.name == self._lastEmittedStartTagName:
                    self.switchStateTo(self.State.Data)
                    self._emitCurrentToken()
                else:
                    elseCase()
            elif charIsUppercaseAlpha(self._currentInputChar):
                self._currentToken.appendCharToTokenName(self._currentInputChar.lower())
                self._temporaryBuffer.append(self._currentInputChar)
            elif charIsLowercaseAlpha(self._currentInputChar):
                self._currentToken.appendCharToTokenName(self._currentInputChar)
                self._temporaryBuffer.append(self._currentInputChar)
            else:
                elseCase()

        def handleRAWTEXTLessThanSign() -> None:
            if self._currentInputChar == "/":
                self._temporaryBuffer = []
                self.switchStateTo(self.State.RAWTEXTEndTagOpen)
            else:
                self._currentToken = cast(HTMLCommentOrCharacter, self._createNewToken(HTMLToken.TokenType.Character))
                self._currentToken.data = "<"
                self._emitCurrentToken()
                self._reconsumeIn(self.State.RAWTEXT)

        def handleRAWTEXTEndTagOpen() -> None:
            if charIsAlpha(self._currentInputChar):
                self._currentToken = self._createNewToken(HTMLToken.TokenType.EndTag)
                self._currentToken.name = ""
                self._reconsumeIn(self.State.RAWTEXTEndTagName)
            else:
                self._currentToken = cast(HTMLCommentOrCharacter, self._createNewToken(HTMLToken.TokenType.Character))
                self._currentToken.data = "<"
                self._emitCurrentToken()
                self._currentToken = cast(HTMLCommentOrCharacter, self._createNewToken(HTMLToken.TokenType.Character))
                self._currentToken.data = "/"
                self._emitCurrentToken()
                self._reconsumeIn(self.State.RAWTEXT)

        def handleRAWTEXTEndTagName() -> None:
            def elseCase():
                self._currentToken = cast(HTMLCommentOrCharacter, self._createNewToken(HTMLToken.TokenType.Character))
                self._currentToken.data = "<"
                self._emitCurrentToken()
                self._currentToken = cast(HTMLCommentOrCharacter, self._createNewToken(HTMLToken.TokenType.Character))
                self._currentToken.data = "/"
                self._emitCurrentToken()

                for char in self._temporaryBuffer:
                    self._currentToken = cast(HTMLCommentOrCharacter,
                                              self._createNewToken(HTMLToken.TokenType.Character))
                    self._currentToken.data = char
                    self._emitCurrentToken()
                self._reconsumeIn(self.State.RAWTEXT)

            if charIsWhitespace(self._currentInputChar):
                if self._currentToken.name == self._lastEmittedStartTagName:
                    self.switchStateTo(self.State.BeforeAttributeName)
                else:
                    elseCase()
            elif self._currentInputChar == "/":
                if self._currentToken.name == self._lastEmittedStartTagName:
                    self.switchStateTo(self.State.SelfClosingStartTag)
                else:
                    elseCase()
            elif self._currentInputChar == ">":
                if self._currentToken.name == self._lastEmittedStartTagName:
                    self.switchStateTo(self.State.Data)
                    self._emitCurrentToken()
                else:
                    elseCase()
            elif charIsUppercaseAlpha(self._currentInputChar):
                self._currentToken.appendCharToTokenName(self._currentInputChar.lower())
                self._temporaryBuffer.append(self._currentInputChar)
            elif charIsLowercaseAlpha(self._currentInputChar):
                self._currentToken.appendCharToTokenName(self._currentInputChar)
                self._temporaryBuffer.append(self._currentInputChar)
            else:
                elseCase()

        def handleScriptDataLessThanSign() -> None:
            if self._currentInputChar == "/":
                self._temporaryBuffer = []
                self.switchStateTo(self.State.ScriptDataEndTagOpen)
            elif self._currentInputChar == "!":
                self.switchStateTo(self.State.ScriptDataEscapeStart)
                self._currentToken = cast(HTMLCommentOrCharacter, self._createNewToken(HTMLToken.TokenType.Character))
                self._currentToken.data = "<"
                self._emitCurrentToken()
                self._currentToken = cast(HTMLCommentOrCharacter, self._createNewToken(HTMLToken.TokenType.Character))
                self._currentToken.data = "!"
                self._emitCurrentToken()
            else:
                self._currentToken = cast(HTMLCommentOrCharacter, self._createNewToken(HTMLToken.TokenType.Character))
                self._currentToken.data = "<"
                self._emitCurrentToken()
                self._reconsumeIn(self.State.ScriptData)

        def handleScriptDataEndTagOpen() -> None:
            if charIsUppercaseAlpha(self._currentInputChar) or charIsLowercaseAlpha(self._currentInputChar):
                self._currentToken = cast(HTMLTag, self._createNewToken(HTMLToken.TokenType.EndTag))
                self._currentToken.name = ""
                self._reconsumeIn(self.State.ScriptDataEndTagName)
            else:
                self._currentToken = cast(HTMLCommentOrCharacter, self._createNewToken(HTMLToken.TokenType.Character))
                self._currentToken.data = "<"
                self._emitCurrentToken()
                self._currentToken = cast(HTMLCommentOrCharacter, self._createNewToken(HTMLToken.TokenType.Character))
                self._currentToken.data = "/"
                self._emitCurrentToken()
                self._reconsumeIn(self.State.ScriptData)

        def handleScriptDataEndTagName() -> None:
            def elseCase() -> None:
                self._currentToken = cast(HTMLCommentOrCharacter, self._createNewToken(HTMLToken.TokenType.Character))
                self._currentToken.data = "<"
                self._emitCurrentToken()
                self._currentToken = cast(HTMLCommentOrCharacter, self._createNewToken(HTMLToken.TokenType.Character))
                self._currentToken.data = "/"
                self._emitCurrentToken()
                for char in self._temporaryBuffer:
                    self._currentToken = cast(HTMLCommentOrCharacter,
                                              self._createNewToken(HTMLToken.TokenType.Character))
                    self._currentToken.data = char
                    self._emitCurrentToken()
                self._reconsumeIn(self.State.ScriptData)

            if charIsWhitespace(self._currentInputChar):
                if self._currentToken.name == self._lastEmittedStartTagName:
                    self.switchStateTo(self.State.BeforeAttributeName)
                else:
                    elseCase()
            elif self._currentInputChar == "/":
                if self._currentToken.name == self._lastEmittedStartTagName:
                    self.switchStateTo(self.State.SelfClosingStartTag)
                else:
                    elseCase()
            elif self._currentInputChar == ">":
                if self._currentToken.name == self._lastEmittedStartTagName:
                    self.switchStateTo(self.State.Data)
                    self._emitCurrentToken()
                else:
                    elseCase()
            elif charIsUppercaseAlpha(self._currentInputChar):
                self._currentToken.appendCharToTokenName(self._currentInputChar.lower())
                self._temporaryBuffer.append(self._currentInputChar)
            elif charIsLowercaseAlpha(self._currentInputChar):
                self._currentToken.appendCharToTokenName(self._currentInputChar)
                self._temporaryBuffer.append(self._currentInputChar)
            else:
                elseCase()

        def handleScriptDataEscapeStart() -> None:
            raise NotImplementedError

        def handleScriptDataEscapeStartDash() -> None:
            raise NotImplementedError

        def handleScriptDataEscaped() -> None:
            raise NotImplementedError

        def handleScriptDataEscapedDash() -> None:
            raise NotImplementedError

        def handleScriptDataEscapedDashDash() -> None:
            raise NotImplementedError

        def handleScriptDataEscapedLessThanSign() -> None:
            raise NotImplementedError

        def handleScriptDataEscapedEndTagOpen() -> None:
            raise NotImplementedError

        def handleScriptDataEscapedEndTagName() -> None:
            raise NotImplementedError

        def handleScriptDataDoubleEscapeStart() -> None:
            raise NotImplementedError

        def handleScriptDataDoubleEscaped() -> None:
            raise NotImplementedError

        def handleScriptDataDoubleEscapedDash() -> None:
            raise NotImplementedError

        def handleScriptDataDoubleEscapedDashDash() -> None:
            raise NotImplementedError

        def handleScriptDataDoubleEscapedLessThanSign() -> None:
            raise NotImplementedError

        def handleScriptDataDoubleEscapeEnd() -> None:
            raise NotImplementedError

        def handleBeforeAttributeName() -> None:
            self._currentToken = cast(HTMLTag, self._currentToken)

            if self._currentInputChar is None:
                self._reconsumeIn(self.State.AfterAttributeName)
            elif charIsWhitespace(self._currentInputChar):
                self._continueIn(self.State.BeforeAttributeName)
            else:
                self._currentToken.createNewAttribute()
                self._reconsumeIn(self.State.AttributeName)

        def handleAttributeName() -> None:
            self._currentToken = cast(HTMLTag, self._currentToken)

            if (
                    self._currentInputChar is None
                    or charIsWhitespace(self._currentInputChar)
                    or self._currentInputChar == "/"
                    or self._currentInputChar == ">"
            ):
                self._reconsumeIn(self.State.AfterAttributeName)
            elif self._currentInputChar == "=":
                self.switchStateTo(self.State.BeforeAttributeValue)
            elif self._currentInputChar.isupper() and self._currentInputChar.isalpha():
                self._currentToken.addCharToAttributeName(self._currentInputChar.lower())
            else:
                self._currentToken.addCharToAttributeName(self._currentInputChar)
                self._continueIn(self.State.AttributeName)

        def handleAfterAttributeName() -> None:
            if charIsWhitespace(self._currentInputChar):
                pass
            elif self._currentInputChar == "/":
                self.switchStateTo(self.State.SelfClosingStartTag)
            elif self._currentInputChar == "=":
                self.switchStateTo(self.State.BeforeAttributeValue)
            elif self._currentInputChar == ">":
                self.switchStateTo(self.State.Data)
                self._emitCurrentToken()
            elif self._currentInputChar is None:
                raise NotImplementedError
            else:
                self._currentToken.createNewAttribute()
                self._reconsumeIn(self.State.AttributeName)

        def handleBeforeAttributeValue() -> None:
            if charIsWhitespace(self._currentInputChar):
                self._continueIn(self.State.BeforeAttributeValue)
            elif self._currentInputChar == '"':
                self.switchStateTo(self.State.AttributeValueDoubleQuoted)
            elif self._currentInputChar == "'":
                self.switchStateTo(self.State.AttributeValueSingleQuoted)
            elif self._currentInputChar == ">":
                self.switchStateTo(self.State.Data)
                self._emitCurrentToken()
            else:
                self._reconsumeIn(self.State.AttributeValueUnquoted)

        def handleAttributeValueDoubleQuoted() -> None:
            self._currentToken = cast(HTMLTag, self._currentToken)
            if self._currentInputChar is None:
                self._currentToken = self._createNewToken(HTMLToken.TokenType.EOF)
                self._emitCurrentToken()
            elif self._currentInputChar == '"':
                self.switchStateTo(self.State.AfterAttributeValueQuoted)
            elif self._currentInputChar == "&":
                self._returnState = self.State.AttributeValueDoubleQuoted
                self.switchStateTo(self.State.CharacterReference)
            else:
                self._currentToken.addCharToAttributeValue(self._currentInputChar)
                self._continueIn(self.State.AttributeValueDoubleQuoted)

        def handleAttributeValueSingleQuoted() -> None:
            self._currentToken = cast(HTMLTag, self._currentToken)
            if self._currentInputChar is None:
                self._currentToken = self._createNewToken(HTMLToken.TokenType.EOF)
                self._emitCurrentToken()
            elif self._currentInputChar == "'":
                self.switchStateTo(self.State.AfterAttributeValueQuoted)
            elif self._currentInputChar == "&":
                self._returnState = self.State.AttributeValueSingleQuoted
                self.switchStateTo(self.State.CharacterReference)
            else:
                self._currentToken.addCharToAttributeValue(self._currentInputChar)
                self._continueIn(self.State.AttributeValueSingleQuoted)

        def handleAttributeValueUnquoted() -> None:
            self._currentToken = cast(HTMLTag, self._currentToken)
            if self._currentInputChar is None:
                self._currentToken = self._createNewToken(HTMLToken.TokenType.EOF)
                self._emitCurrentToken()
            elif charIsWhitespace(self._currentInputChar):
                self.switchStateTo(self.State.BeforeAttributeName)
            elif self._currentInputChar == "&":
                self._returnState = self.State.AttributeValueUnquoted
                self.switchStateTo(self.State.CharacterReference)
            elif self._currentInputChar == ">":
                self.switchStateTo(self.State.Data)
                self._emitCurrentToken()
            else:
                self._currentToken.addCharToAttributeValue(self._currentInputChar)
                self._continueIn(self.State.AttributeValueUnquoted)

        def handleAfterAttributeValueQuoted() -> None:
            if self._currentInputChar is None:
                self._currentToken = self._createNewToken(HTMLToken.TokenType.EOF)
                self._emitCurrentToken()
            elif charIsWhitespace(self._currentInputChar):
                self.switchStateTo(self.State.BeforeAttributeName)
            elif self._currentInputChar == "/":
                self.switchStateTo(self.State.SelfClosingStartTag)
            elif self._currentInputChar == ">":
                self.switchStateTo(self.State.Data)
                self._emitCurrentToken()
            else:
                self._reconsumeIn(self.State.BeforeAttributeName)

        def handleSelfClosingStartTag() -> None:
            if self._currentInputChar == ">":
                self._currentToken.selfClosing = True
                self.switchStateTo(self.State.Data)
                self._emitCurrentToken()
            elif self._currentInputChar is None:
                self._currentToken = self._createNewToken(HTMLToken.TokenType.EOF)
                self._emitCurrentToken()
            else:
                self._reconsumeIn(self.State.BeforeAttributeName)

        def handleBogusComment() -> None:
            raise NotImplementedError

        def handleMarkupDeclarationOpen() -> None:
            if self._nextCharactersAre("--"):
                self._consumeCharacters("--")
                self._currentToken = self._createNewToken(HTMLToken.TokenType.Comment)
                self.switchStateTo(self.State.CommentStart)
            elif self._nextCharactersAre("DOCTYPE"):
                self._consumeCharacters("DOCTYPE")
                self.switchStateTo(self.State.DOCTYPE)

        def handleCommentStart() -> None:

            if self._currentInputChar == "-":
                self.switchStateTo(self.State.CommentStartDash)
            elif self._currentInputChar == ">":
                self.switchStateTo(self.State.Data)
                self._emitCurrentToken()
            else:
                self._reconsumeIn(self.State.Comment)

        def handleCommentStartDash() -> None:
            self._currentToken = cast(HTMLCommentOrCharacter, self._currentToken)
            if self._currentInputChar == "-":
                self.switchStateTo(self.State.CommentEnd)
            elif self._currentInputChar == ">":
                self.switchStateTo(self.State.Data)
                self._emitCurrentToken()
            elif self._currentInputChar is None:
                self._emitCurrentToken()
                self._currentToken = self._createNewToken(HTMLToken.TokenType.EOF)
                self._emitCurrentToken()
            else:
                if self._currentToken.data is not None:
                    self._currentToken.data += "-"
                else:
                    self._currentToken.data = "-"
                self._reconsumeIn(self.State.Comment)

        def handleComment() -> None:
            self._currentToken = cast(HTMLCommentOrCharacter, self._currentToken)
            if self._currentInputChar == "-":
                self.switchStateTo(self.State.CommentEndDash)
            elif self._currentInputChar is None:
                self._emitCurrentToken()
                self._currentToken = self._createNewToken(HTMLToken.TokenType.EOF)
                self._emitCurrentToken()
            else:
                if self._currentToken.data is not None:
                    self._currentToken.data += self._currentInputChar
                else:
                    self._currentToken.data = self._currentInputChar
                self._continueIn(self.State.Comment)

        def handleCommentLessThanSign() -> None:
            raise NotImplementedError

        def handleCommentLessThanSignBang() -> None:
            raise NotImplementedError

        def handleCommentLessThanSignBangDash() -> None:
            raise NotImplementedError

        def handleCommentLessThanSignBangDashDash() -> None:
            raise NotImplementedError

        def handleCommentEndDash() -> None:
            self._currentToken = cast(HTMLCommentOrCharacter, self._currentToken)
            if self._currentInputChar == "-":
                self.switchStateTo(self.State.CommentEnd)
            elif self._currentInputChar is None:
                self._emitCurrentToken()
                self._currentToken = self._createNewToken(HTMLToken.TokenType.EOF)
                self._emitCurrentToken()
            else:
                if self._currentToken.data is not None:
                    self._currentToken.data += "-"
                else:
                    self._currentToken.data = "-"
                self._reconsumeIn(self.State.Comment)

        def handleCommentEnd() -> None:
            self._currentToken = cast(HTMLCommentOrCharacter, self._currentToken)
            if self._currentInputChar == ">":
                self.switchStateTo(self.State.Data)
                self._emitCurrentToken()
            elif self._currentInputChar == "-":
                if self._currentToken.data is not None:
                    self._currentToken.data += "-"
                else:
                    self._currentToken.data = "-"
                self._continueIn(self.State.CommentEnd)
            elif self._currentInputChar is None:
                self._emitCurrentToken()
                self._currentToken = self._createNewToken(HTMLToken.TokenType.EOF)
                self._emitCurrentToken()
            else:
                if self._currentToken.data is not None:
                    self._currentToken.data += "-"
                else:
                    self._currentToken.data = "-"
                self._reconsumeIn(self.State.Comment)

        def handleCommentEndBang() -> None:
            raise NotImplementedError

        def handleDOCTYPE() -> None:
            if charIsWhitespace(cast(str, self._currentInputChar)):
                self.switchStateTo(self.State.BeforeDOCTYPEName)

        def handleBeforeDOCTYPEName() -> None:
            if charIsWhitespace(cast(str, self._currentInputChar)):
                self._ignoreCharacterAndContinueTo(self.State.BeforeDOCTYPEName)
            else:
                self._currentToken = cast(HTMLDoctype, self._createNewToken(HTMLToken.TokenType.DOCTYPE))
                if self._currentToken.name is not None and self._currentInputChar is not None:
                    self._currentToken.name += self._currentInputChar
                else:
                    self._currentToken.name = self._currentInputChar

                self.switchStateTo(self.State.DOCTYPEName)

        def handleDOCTYPEName() -> None:
            self._currentToken = cast(HTMLDoctype, self._currentToken)
            if self._currentInputChar == ">":
                self.switchStateTo(self.State.Data)
                self._emitCurrentToken()
            else:
                self._currentToken.name = self._currentToken.name + str(self._currentInputChar)
                self._continueIn(self.State.DOCTYPEName)

        def handleAfterDOCTYPEName() -> None:
            raise NotImplementedError

        def handleAfterDOCTYPEPublicKeyword() -> None:
            raise NotImplementedError

        def handleBeforeDOCTYPEPublicIdentifier() -> None:
            raise NotImplementedError

        def handleDOCTYPEPublicIdentifierDoubleQuoted() -> None:
            raise NotImplementedError

        def handleDOCTYPEPublicIdentifierSingleQuoted() -> None:
            raise NotImplementedError

        def handleAfterDOCTYPEPublicIdentifier() -> None:
            raise NotImplementedError

        def handleBetweenDOCTYPEPublicAndSystemIdentifiers() -> None:
            raise NotImplementedError

        def handleAfterDOCTYPESystemKeyword() -> None:
            raise NotImplementedError

        def handleBeforeDOCTYPESystemIdentifier() -> None:
            raise NotImplementedError

        def handleDOCTYPESystemIdentifierDoubleQuoted() -> None:
            raise NotImplementedError

        def handleDOCTYPESystemIdentifierSingleQuoted() -> None:
            raise NotImplementedError

        def handleAfterDOCTYPESystemIdentifier() -> None:
            raise NotImplementedError

        def handleBogusDOCTYPE() -> None:
            raise NotImplementedError

        def handleCDATASection() -> None:
            raise NotImplementedError

        def handleCDATASectionBracket() -> None:
            raise NotImplementedError

        def handleCDATASectionEnd() -> None:
            raise NotImplementedError

        def handleCharacterReference() -> None:
            self._temporaryBuffer.append("&")
            if self._currentInputChar.isalnum():
                self._reconsumeIn(self.State.NamedCharacterReference)
            elif self._currentInputChar == "#":
                self._temporaryBuffer.append(self._currentInputChar)
                self.switchStateTo(self.State.NumericCharacterReference)
            else:
                self._flushTemporaryBuffer()
                self._reconsumeIn(self._returnState)

        def handleNamedCharacterReference() -> None:
            consumedCharacters: List[str] = [self._currentInputChar]
            while atLeastOneNameStartsWith("".join(consumedCharacters)):
                nextChar = self._nextCodePoint()
                self._currentInputChar = nextChar
                consumedCharacters.append(nextChar)
                if nextChar == ";":
                    break
            match = getNamedCharFromTable("".join(consumedCharacters))
            if match is not None:
                # TODO: Implement case.
                if self._currentToken is not None:
                    self._currentToken.addCharToAttributeValue(chr(match))
                else:
                    self._currentToken = cast(HTMLCommentOrCharacter,
                                              self._createNewToken(HTMLToken.TokenType.Character))
                    self._currentToken.data = chr(match)
                    self._emitCurrentToken()
                self.switchStateTo(self._returnState)
            else:
                self._temporaryBuffer.extend(consumedCharacters)
                self._flushTemporaryBuffer()
                self._reconsumeIn(self.State.AmbiguousAmpersand)

        def handleAmbiguousAmpersand() -> None:
            if self._currentInputChar.isalnum():
                self._temporaryBuffer.append(self._currentInputChar)
                self._flushTemporaryBuffer()
            elif self._currentInputChar == ";":
                self._reconsumeIn(self._returnState)
            else:
                self._reconsumeIn(self._returnState)

        def handleNumericCharacterReference() -> None:
            characterReferenceCode = 0

            if self._currentInputChar == "X" or self._currentInputChar == "x":
                self._temporaryBuffer.append(self._currentInputChar)
                self.switchStateTo(self.State.HexadecimalCharacterReferenceStart)
            else:
                self._reconsumeIn(self.State.DecimalCharacterReferenceStart)

        def handleHexadecimalCharacterReferenceStart() -> None:
            raise NotImplementedError

        def handleDecimalCharacterReferenceStart() -> None:
            if self._currentInputChar.isdigit():
                self._reconsumeIn(self.State.HexadecimalCharacterReference)
            else:
                # TODO: handle parse error.
                self._flushTemporaryBuffer()
                self._reconsumeIn(self._returnState)

        def handleHexadecimalCharacterReference() -> None:
            if self._currentInputChar.isdigit():
                self._characterReferenceCode *= 16
                self._characterReferenceCode += ord(self._currentInputChar) - 0x0030
            elif charIsUppercaseAlpha(self._currentInputChar):
                self._characterReferenceCode *= 16
                self._characterReferenceCode += ord(self._currentInputChar) - 0x0037
            elif charIsLowercaseAlpha(self._currentInputChar):
                self._characterReferenceCode *= 16
                self._characterReferenceCode += ord(self._currentInputChar) - 0x0057
            elif self._currentInputChar == ";":
                self.switchStateTo(self.State.NumericCharacterReferenceEnd)
            else:
                # TODO: Handle parse error.
                self._reconsumeIn(self.state.NumericCharacterReferenceEnd)

        def handleDecimalCharacterReference() -> None:
            raise NotImplementedError

        def handleNumericCharacterReferenceEnd() -> None:
            if self._characterReferenceCode == 0:
                # TODO: handle parse error.
                self._characterReferenceCode = 0xFFFD
            elif self._characterReferenceCode > 0x10ffff:
                # TODO: handle parse error.
                self._characterReferenceCode = 0xFFFD
            elif charIsSurrogate(self._characterReferenceCode):
                # TODO: handle parse error.
                self._characterReferenceCode = 0xFFFD
            elif charIsNoncharacter(self._characterReferenceCode):
                # TODO: Handle parse error.
                pass
            elif self._characterReferenceCode == 0x0D or (
                    charIsControl(self._characterReferenceCode) and not charIsWhitespace(
                    chr(self.characterReferenceCode))):
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
                value = conversionTable.get(self._characterReferenceCode, None)
                if value is not None:
                    self._characterReferenceCode = value

            self._temporaryBuffer = []
            self._temporaryBuffer.append(chr(self._characterReferenceCode))
            self._flushTemporaryBuffer()
            self.switchStateTo(self._returnState)

        switcher = {
            self.State.Data: handleData,
            self.State.RCDATA: handleRCDATA,
            self.State.RAWTEXT: handleRAWTEXT,
            self.State.ScriptData: handleScriptData,
            self.State.PLAINTEXT: handlePLAINTEXT,
            self.State.TagOpen: handleTagOpen,
            self.State.EndTagOpen: handleEndTagOpen,
            self.State.TagName: handleTagName,
            self.State.RCDATALessThanSign: handleRCDATALessThanSign,
            self.State.RCDATAEndTagOpen: handleRCDATAEndTagOpen,
            self.State.RCDATAEndTagName: handleRCDATAEndTagName,
            self.State.RAWTEXTLessThanSign: handleRAWTEXTLessThanSign,
            self.State.RAWTEXTEndTagOpen: handleRAWTEXTEndTagOpen,
            self.State.RAWTEXTEndTagName: handleRAWTEXTEndTagName,
            self.State.ScriptDataLessThanSign: handleScriptDataLessThanSign,
            self.State.ScriptDataEndTagOpen: handleScriptDataEndTagOpen,
            self.State.ScriptDataEndTagName: handleScriptDataEndTagName,
            self.State.ScriptDataEscapeStart: handleScriptDataEscapeStart,
            self.State.ScriptDataEscapeStartDash: handleScriptDataEscapeStartDash,
            self.State.ScriptDataEscaped: handleScriptDataEscaped,
            self.State.ScriptDataEscapedDash: handleScriptDataEscapedDash,
            self.State.ScriptDataEscapedDashDash: handleScriptDataEscapedDashDash,
            self.State.ScriptDataEscapedLessThanSign: handleScriptDataEscapedLessThanSign,
            self.State.ScriptDataEscapedEndTagOpen: handleScriptDataEscapedEndTagOpen,
            self.State.ScriptDataEscapedEndTagName: handleScriptDataEscapedEndTagName,
            self.State.ScriptDataDoubleEscapeStart: handleScriptDataDoubleEscapeStart,
            self.State.ScriptDataDoubleEscaped: handleScriptDataDoubleEscaped,
            self.State.ScriptDataDoubleEscapedDash: handleScriptDataDoubleEscapedDash,
            self.State.ScriptDataDoubleEscapedDashDash: handleScriptDataDoubleEscapedDashDash,
            self.State.ScriptDataDoubleEscapedLessThanSign: handleScriptDataDoubleEscapedLessThanSign,
            self.State.ScriptDataDoubleEscapeEnd: handleScriptDataDoubleEscapeEnd,
            self.State.BeforeAttributeName: handleBeforeAttributeName,
            self.State.AttributeName: handleAttributeName,
            self.State.AfterAttributeName: handleAfterAttributeName,
            self.State.BeforeAttributeValue: handleBeforeAttributeValue,
            self.State.AttributeValueDoubleQuoted: handleAttributeValueDoubleQuoted,
            self.State.AttributeValueSingleQuoted: handleAttributeValueSingleQuoted,
            self.State.AttributeValueUnquoted: handleAttributeValueUnquoted,
            self.State.AfterAttributeValueQuoted: handleAfterAttributeValueQuoted,
            self.State.SelfClosingStartTag: handleSelfClosingStartTag,
            self.State.BogusComment: handleBogusComment,
            self.State.MarkupDeclarationOpen: handleMarkupDeclarationOpen,
            self.State.CommentStart: handleCommentStart,
            self.State.CommentStartDash: handleCommentStartDash,
            self.State.Comment: handleComment,
            self.State.CommentLessThanSign: handleCommentLessThanSign,
            self.State.CommentLessThanSignBang: handleCommentLessThanSignBang,
            self.State.CommentLessThanSignBangDash: handleCommentLessThanSignBangDash,
            self.State.CommentLessThanSignBangDashDash: handleCommentLessThanSignBangDashDash,
            self.State.CommentEndDash: handleCommentEndDash,
            self.State.CommentEnd: handleCommentEnd,
            self.State.CommentEndBang: handleCommentEndBang,
            self.State.DOCTYPE: handleDOCTYPE,
            self.State.BeforeDOCTYPEName: handleBeforeDOCTYPEName,
            self.State.DOCTYPEName: handleDOCTYPEName,
            self.State.AfterDOCTYPEName: handleAfterDOCTYPEName,
            self.State.AfterDOCTYPEPublicKeyword: handleAfterDOCTYPEPublicKeyword,
            self.State.BeforeDOCTYPEPublicIdentifier: handleBeforeDOCTYPEPublicIdentifier,
            self.State.DOCTYPEPublicIdentifierDoubleQuoted: handleDOCTYPEPublicIdentifierDoubleQuoted,
            self.State.DOCTYPEPublicIdentifierSingleQuoted: handleDOCTYPEPublicIdentifierSingleQuoted,
            self.State.AfterDOCTYPEPublicIdentifier: handleAfterDOCTYPEPublicIdentifier,
            self.State.BetweenDOCTYPEPublicAndSystemIdentifiers: handleBetweenDOCTYPEPublicAndSystemIdentifiers,
            self.State.AfterDOCTYPESystemKeyword: handleAfterDOCTYPESystemKeyword,
            self.State.BeforeDOCTYPESystemIdentifier: handleBeforeDOCTYPESystemIdentifier,
            self.State.DOCTYPESystemIdentifierDoubleQuoted: handleDOCTYPESystemIdentifierDoubleQuoted,
            self.State.DOCTYPESystemIdentifierSingleQuoted: handleDOCTYPESystemIdentifierSingleQuoted,
            self.State.AfterDOCTYPESystemIdentifier: handleAfterDOCTYPESystemIdentifier,
            self.State.BogusDOCTYPE: handleBogusDOCTYPE,
            self.State.CDATASection: handleCDATASection,
            self.State.CDATASectionBracket: handleCDATASectionBracket,
            self.State.CDATASectionEnd: handleCDATASectionEnd,
            self.State.CharacterReference: handleCharacterReference,
            self.State.NamedCharacterReference: handleNamedCharacterReference,
            self.State.AmbiguousAmpersand: handleAmbiguousAmpersand,
            self.State.NumericCharacterReference: handleNumericCharacterReference,
            self.State.HexadecimalCharacterReferenceStart: handleHexadecimalCharacterReferenceStart,
            self.State.DecimalCharacterReferenceStart: handleDecimalCharacterReferenceStart,
            self.State.HexadecimalCharacterReference: handleHexadecimalCharacterReference,
            self.State.DecimalCharacterReference: handleDecimalCharacterReference,
            self.State.NumericCharacterReferenceEnd: handleNumericCharacterReferenceEnd,
        }

        return switcher.get(self.state, None)

    def run(self) -> None:
        while self._cursor < len(self._html):
            self._currentInputChar = self._nextCodePoint()
            switcher = self._getStateSwitcher()
            if switcher is not None:
                switcher()

        self._currentInputChar = None
        switcher = self._getStateSwitcher()
        if switcher is not None:
            switcher()
