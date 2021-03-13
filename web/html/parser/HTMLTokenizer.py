from enum import Enum, auto
from typing import Union, Callable, Any, cast, List
from HTMLToken import HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter
from utils import charIsAlpha, charIsControl, charIsNoncharacter, charIsWhitespace, charIsUppercaseAlpha, \
    charIsLowercaseAlpha, charIsSurrogate
from Entities import getNamedCharFromTable, atLeastOneNameStartsWith


class HTMLTokenizer:

    def __init__(self, html: str, tokenHandlerCb: Callable[[HTMLToken], None]):
        self.state = self.State.Data
        self.__html = html
        self.__cursor = 0
        self.__currentInputChar: Union[str, None] = None
        self.__returnState: Union[Any, None] = None
        self.__currentToken: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter, None] = None
        self.__tokenHandlerCb: Callable[[HTMLToken], None] = tokenHandlerCb
        self.__temporaryBuffer: List[str] = []
        self.__characterReferenceCode: int = 0
        self.__lastEmittedStartTagName: str = None

    def __emitCurrentToken(self) -> None:
        self.__tokenHandlerCb(self.__currentToken)
        if self.__currentToken.type == HTMLToken.TokenType.StartTag:
            self.__lastEmittedStartTagName = self.__currentToken.name
        self.__currentToken = None
        print("Current state: ", self.state)

    def __createNewToken(
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
            return
        char = self.__html[self.__cursor]
        self.__cursor += 1
        return char

    def __flushTemporaryBuffer(self) -> None:
        if self.__currentToken is not None:
            self.__currentToken.addCharToAttributeValue("".join(self.__temporaryBuffer))
        else:
            for char in self.__temporaryBuffer:
                self.__currentToken = cast(HTMLCommentOrCharacter, self.__createNewToken(HTMLToken.TokenType.Character))
                self.__currentToken.data = char
                self.__emitCurrentToken()
        self.__temporaryBuffer = []

    def __getStateSwitcher(self) -> Union[Callable[[], None], None]:
        def handleData() -> None:
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

        def handleRCDATA() -> None:
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

        def handleRAWTEXT() -> None:
            if self.__currentInputChar == "<":
                self.switchStateTo(self.State.RAWTEXTLessThanSign)
            elif self.__currentInputChar is None:
                self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
                self.__emitCurrentToken()
            else:
                self.__currentToken = cast(HTMLCommentOrCharacter, self.__createNewToken(HTMLToken.TokenType.Character))
                self.__currentToken.data = self.__currentInputChar
                self.__emitCurrentToken()

        def handleScriptData() -> None:
            if self.__currentInputChar == "<":
                self.switchStateTo(self.State.ScriptDataLessThanSign)
            elif self.__currentInputChar is None:
                self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
                self.__emitCurrentToken()
            else:
                self.__currentToken = cast(HTMLCommentOrCharacter, self.__createNewToken(HTMLToken.TokenType.Character))
                self.__currentToken.data = self.__currentInputChar
                self.__emitCurrentToken()

        def handlePLAINTEXT() -> None:
            raise NotImplementedError

        def handleTagOpen() -> None:
            if self.__currentInputChar == "!":
                self.__reconsumeIn(self.State.MarkupDeclarationOpen)
            elif self.__currentInputChar == "/":
                self.switchStateTo(self.State.EndTagOpen)
            elif self.__currentInputChar.isalpha():
                self.__currentToken = cast(HTMLTag, self.__createNewToken(HTMLToken.TokenType.StartTag))
                self.__reconsumeIn(self.State.TagName)

        def handleEndTagOpen() -> None:
            self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EndTag)
            self.__reconsumeIn(self.State.TagName)

        def handleTagName() -> None:
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

        def handleRCDATALessThanSign() -> None:
            if self.__currentInputChar == "/":
                self.__temporaryBuffer = []
                self.switchStateTo(self.State.RCDATAEndTagOpen)
            else:
                self.__currentToken = cast(HTMLCommentOrCharacter, self.__createNewToken(HTMLToken.TokenType.Character))
                self.__currentToken.data = "<"
                self.__emitCurrentToken()
                self.__reconsumeIn(self.State.RCDATA)

        def handleRCDATAEndTagOpen() -> None:
            if charIsAlpha(self.__currentInputChar):
                self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EndTag)
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

        def handleRCDATAEndTagName() -> None:
            print("Current char:", self.__currentInputChar)
            print("Current token:", self.__currentToken)
            print("Last emited token:", self.__lastEmittedStartTagName)

            def elseCase():
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

        def handleRAWTEXTLessThanSign() -> None:
            if self.__currentInputChar == "/":
                self.__temporaryBuffer = []
                self.switchStateTo(self.State.RAWTEXTEndTagOpen)
            else:
                self.__currentToken = cast(HTMLCommentOrCharacter, self.__createNewToken(HTMLToken.TokenType.Character))
                self.__currentToken.data = "<"
                self.__emitCurrentToken()
                self.__reconsumeIn(self.State.RAWTEXT)

        def handleRAWTEXTEndTagOpen() -> None:
            if charIsAlpha(self.__currentInputChar):
                self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EndTag)
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

        def handleRAWTEXTEndTagName() -> None:
            def elseCase():
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

        def handleScriptDataLessThanSign() -> None:
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

        def handleScriptDataEndTagOpen() -> None:
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

        def handleScriptDataEndTagName() -> None:
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
            self.__currentToken = cast(HTMLTag, self.__currentToken)

            if self.__currentInputChar is None:
                self.__reconsumeIn(self.State.AfterAttributeName)
            elif charIsWhitespace(self.__currentInputChar):
                self.__continueIn(self.State.BeforeAttributeName)
            else:
                self.__currentToken.createNewAttribute()
                self.__reconsumeIn(self.State.AttributeName)

        def handleAttributeName() -> None:
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

        def handleAfterAttributeName() -> None:
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

        def handleBeforeAttributeValue() -> None:
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

        def handleAttributeValueDoubleQuoted() -> None:
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

        def handleAttributeValueSingleQuoted() -> None:
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

        def handleAttributeValueUnquoted() -> None:
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

        def handleAfterAttributeValueQuoted() -> None:
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

        def handleSelfClosingStartTag() -> None:
            if self.__currentInputChar == ">":
                self.__currentToken.selfClosing = True
                self.switchStateTo(self.State.Data)
                self.__emitCurrentToken()
            elif self.__currentInputChar is None:
                self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
                self.__emitCurrentToken()
            else:
                self.__reconsumeIn(self.State.BeforeAttributeName)

        def handleBogusComment() -> None:
            raise NotImplementedError

        def handleMarkupDeclarationOpen() -> None:
            if self.__nextCharactersAre("--"):
                self.__consumeCharacters("--")
                self.__currentToken = self.__createNewToken(HTMLToken.TokenType.Comment)
                self.switchStateTo(self.State.CommentStart)
            elif self.__nextCharactersAre("DOCTYPE"):
                self.__consumeCharacters("DOCTYPE")
                self.switchStateTo(self.State.DOCTYPE)

        def handleCommentStart() -> None:

            if self.__currentInputChar == "-":
                self.switchStateTo(self.State.CommentStartDash)
            elif self.__currentInputChar == ">":
                self.switchStateTo(self.State.Data)
                self.__emitCurrentToken()
            else:
                self.__reconsumeIn(self.State.Comment)

        def handleCommentStartDash() -> None:
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

        def handleComment() -> None:
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

        def handleCommentLessThanSign() -> None:
            raise NotImplementedError

        def handleCommentLessThanSignBang() -> None:
            raise NotImplementedError

        def handleCommentLessThanSignBangDash() -> None:
            raise NotImplementedError

        def handleCommentLessThanSignBangDashDash() -> None:
            raise NotImplementedError

        def handleCommentEndDash() -> None:
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

        def handleCommentEnd() -> None:
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

        def handleCommentEndBang() -> None:
            raise NotImplementedError

        def handleDOCTYPE() -> None:
            if charIsWhitespace(cast(str, self.__currentInputChar)):
                self.switchStateTo(self.State.BeforeDOCTYPEName)

        def handleBeforeDOCTYPEName() -> None:
            if charIsWhitespace(cast(str, self.__currentInputChar)):
                self.__ignoreCharacterAndContinueTo(self.State.BeforeDOCTYPEName)
            else:
                self.__currentToken = cast(HTMLDoctype, self.__createNewToken(HTMLToken.TokenType.DOCTYPE))
                if self.__currentToken.name is not None and self.__currentInputChar is not None:
                    self.__currentToken.name += self.__currentInputChar
                else:
                    self.__currentToken.name = self.__currentInputChar

                self.switchStateTo(self.State.DOCTYPEName)

        def handleDOCTYPEName() -> None:
            self.__currentToken = cast(HTMLDoctype, self.__currentToken)
            if self.__currentInputChar == ">":
                self.switchStateTo(self.State.Data)
                self.__emitCurrentToken()
            else:
                self.__currentToken.name = self.__currentToken.name + str(self.__currentInputChar)
                self.__continueIn(self.State.DOCTYPEName)

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
            self.__temporaryBuffer.append("&")
            if self.__currentInputChar.isalnum():
                self.__reconsumeIn(self.State.NamedCharacterReference)
            elif self.__currentInputChar == "#":
                self.__temporaryBuffer.append(self.__currentInputChar)
                self.switchStateTo(self.State.NumericCharacterReference)
            else:
                self.__flushTemporaryBuffer()
                self.__reconsumeIn(self.__returnState)

        def handleNamedCharacterReference() -> None:
            consumedCharacters: List[str] = [self.__currentInputChar]
            while atLeastOneNameStartsWith("".join(consumedCharacters)):
                nextChar = self.__nextCodePoint()
                self.__currentInputChar = nextChar
                consumedCharacters.append(nextChar)
                if nextChar == ";":
                    break
            match = getNamedCharFromTable("".join(consumedCharacters))
            if match is not None:
                # TODO: Implement case.
                if self.__currentToken is not None:
                    self.__currentToken.addCharToAttributeValue(chr(match))
                else:
                    self.__currentToken = cast(HTMLCommentOrCharacter,
                                              self.__createNewToken(HTMLToken.TokenType.Character))
                    self.__currentToken.data = chr(match)
                    self.__emitCurrentToken()
                self.switchStateTo(self.__returnState)
            else:
                self.__temporaryBuffer.extend(consumedCharacters)
                self.__flushTemporaryBuffer()
                self.__reconsumeIn(self.State.AmbiguousAmpersand)

        def handleAmbiguousAmpersand() -> None:
            if self.__currentInputChar.isalnum():
                self.__temporaryBuffer.append(self.__currentInputChar)
                self.__flushTemporaryBuffer()
            elif self.__currentInputChar == ";":
                self.__reconsumeIn(self.__returnState)
            else:
                self.__reconsumeIn(self.__returnState)

        def handleNumericCharacterReference() -> None:
            characterReferenceCode = 0

            if self.__currentInputChar == "X" or self.__currentInputChar == "x":
                self.__temporaryBuffer.append(self.__currentInputChar)
                self.switchStateTo(self.State.HexadecimalCharacterReferenceStart)
            else:
                self.__reconsumeIn(self.State.DecimalCharacterReferenceStart)

        def handleHexadecimalCharacterReferenceStart() -> None:
            raise NotImplementedError

        def handleDecimalCharacterReferenceStart() -> None:
            if self.__currentInputChar.isdigit():
                self.__reconsumeIn(self.State.HexadecimalCharacterReference)
            else:
                # TODO: handle parse error.
                self.__flushTemporaryBuffer()
                self.__reconsumeIn(self.__returnState)

        def handleHexadecimalCharacterReference() -> None:
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
                self.__reconsumeIn(self.state.NumericCharacterReferenceEnd)

        def handleDecimalCharacterReference() -> None:
            raise NotImplementedError

        def handleNumericCharacterReferenceEnd() -> None:
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
                    charIsControl(self.__characterReferenceCode) and not charIsWhitespace(
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
                value = conversionTable.get(self.__characterReferenceCode, None)
                if value is not None:
                    self.__characterReferenceCode = value

            self.__temporaryBuffer = []
            self.__temporaryBuffer.append(chr(self.__characterReferenceCode))
            self.__flushTemporaryBuffer()
            self.switchStateTo(self.__returnState)

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
        while self.__cursor < len(self.__html):
            self.__currentInputChar = self.__nextCodePoint()
            switcher = self.__getStateSwitcher()
            if switcher is not None:
                switcher()

        self.__currentInputChar = None
        switcher = self.__getStateSwitcher()
        if switcher is not None:
            switcher()
