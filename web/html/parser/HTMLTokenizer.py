from enum import Enum, auto
from typing import Union, Callable, Any, cast
from .HTMLToken import HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter
from .utils import charIsWhitespace


class HTMLTokenizer:

    def __emitCurrentToken(self) -> None:
        self.__tokenHandlerCb(self.__currentToken)
        self.__currentToken = None

    def __createNewToken(self, tokenType: HTMLToken.TokenType) -> Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter]:
        token = None
        if (tokenType == HTMLToken.TokenType.DOCTYPE):
            token = HTMLDoctype()
        elif (tokenType == HTMLToken.TokenType.Comment or tokenType == HTMLToken.TokenType.Character):
            token = HTMLCommentOrCharacter(tokenType)
        elif (tokenType == HTMLToken.TokenType.StartTag or tokenType == HTMLToken.TokenType.EndTag):
            token = HTMLTag(tokenType)
        else:
            token = HTMLToken(tokenType)
        return token

    class __State(Enum):
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

    def __continueIn(self, state: __State) -> None:
        self.__switchTo(state)


    def __ignoreCharacterAndContinueTo(self, newState: __State) -> None:
        self.__switchTo(newState)

    def __switchTo(self, newState: __State) -> None:
        '''
        Switch state and consume next character.
        '''
        self.__state = newState
        self.__currentInputChar = self.__nextCodePoint()
        switcher = self.__getStateSwitcher()
        if (switcher != None):
            switcher()

    def __reconsumeIn(self, newState: __State) -> None:
        '''
        Switch state without consuming next character.
        '''
        self.__state = newState
        switcher = self.__getStateSwitcher()
        if (switcher != None):
            switcher()

    
    def __nextCharactersAre(self, characters: str) -> bool:
        for index in range(len(characters)):
            if (self.__cursor >= len(self.__html)):
                return False
            char = self.__html[self.__cursor + index]
            if (char.lower() != characters[index].lower()):
                return False

        return True

    def __consumeCharacters(self, characters: str) -> None:
        self.__cursor += len(characters)


    def __nextCodePoint(self) -> Union[str, None]:
        if (self.__cursor >= len(self.__html)):
            return
        char = self.__html[self.__cursor]
        self.__cursor += 1
        return char

    def __init__(self, html: str, tokenHandlerCb: Callable):
        self.__state = self.__State.Data
        self.__html = html
        self.__cursor = 0
        self.__currentInputChar: Union[str, None] = None
        self.__returnState: Union[Any, None] = None
        self.__currentToken: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter, None] = None
        self.__tokenHandlerCb = tokenHandlerCb

    def __getStateSwitcher(self) -> Union[Callable[[], None], None]:

        def handleData() -> None:
            if (self.__currentInputChar == "&"):
                self.__returnState = self.__State.Data
                self.__switchTo(self.__State.CharacterReference)
            elif (self.__currentInputChar == "<"):
                self.__switchTo(self.__State.TagOpen)
            elif (self.__currentInputChar == None):
                self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
                self.__emitCurrentToken()
                return
            else:
                self.__currentToken = cast(HTMLCommentOrCharacter, self.__createNewToken(HTMLToken.TokenType.Character))
                self.__currentToken.data = self.__currentInputChar
                self.__emitCurrentToken()
                self.__continueIn(self.__State.Data)


        def handleRCDATA() -> None:
            return

        def handleRAWTEXT() -> None:
            return

        def handleScriptData() -> None:
            return

        def handlePLAINTEXT() -> None:
            return

        def handleTagOpen() -> None:
            if (self.__currentInputChar == "!"):
                self.__reconsumeIn(self.__State.MarkupDeclarationOpen)
            elif (self.__currentInputChar == "/"):
                self.__switchTo(self.__State.EndTagOpen)
            elif (self.__currentInputChar.isalpha()):
                self.__currentToken = cast(HTMLTag, self.__createNewToken(HTMLToken.TokenType.StartTag))
                self.__reconsumeIn(self.__State.TagName)

        def handleEndTagOpen() -> None:
            self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EndTag)
            self.__reconsumeIn(self.__State.TagName)
            return


        def handleTagName() -> None:
            if (self.__currentInputChar == None):
                self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
                self.__emitCurrentToken()
            elif (charIsWhitespace(self.__currentInputChar)):
                self.__switchTo(self.__State.BeforeAttributeName)
            elif (self.__currentInputChar == ">"):
                self.__emitCurrentToken()
                self.__switchTo(self.__State.Data)
            else:
                self.__currentToken = cast(HTMLTag, self.__currentToken)
                if (self.__currentToken.name != None and self.__currentInputChar != None):
                    self.__currentToken.name += self.__currentInputChar
                else:
                    self.__currentToken.name = self.__currentInputChar
                self.__continueIn(self.__State.TagName)
            

        def handleRCDATALessThanSign() -> None:
            return

        def handleRCDATAEndTagOpen() -> None:
            return

        def handleRCDATAEndTagName() -> None:
            return

        def handleRAWTEXTLessThanSign() -> None:
            return

        def handleRAWTEXTEndTagOpen() -> None:
            return

        def handleRAWTEXTEndTagName() -> None:
            return

        def handleScriptDataLessThanSign() -> None:
            return

        def handleScriptDataEndTagOpen() -> None:
            return

        def handleScriptDataEndTagName() -> None:
            return

        def handleScriptDataEscapeStart() -> None:
            return

        def handleScriptDataEscapeStartDash() -> None:
            return

        def handleScriptDataEscaped() -> None:
            return

        def handleScriptDataEscapedDash() -> None:
            return

        def handleScriptDataEscapedDashDash() -> None:
            return

        def handleScriptDataEscapedLessThanSign() -> None:
            return

        def handleScriptDataEscapedEndTagOpen() -> None:
            return

        def handleScriptDataEscapedEndTagName() -> None:
            return

        def handleScriptDataDoubleEscapeStart() -> None:
            return

        def handleScriptDataDoubleEscaped() -> None:
            return

        def handleScriptDataDoubleEscapedDash() -> None:
            return

        def handleScriptDataDoubleEscapedDashDash() -> None:
            return

        def handleScriptDataDoubleEscapedLessThanSign() -> None:
            return

        def handleScriptDataDoubleEscapeEnd() -> None:
            return

        def handleBeforeAttributeName() -> None:
            self.__currentToken = cast(HTMLTag, self.__currentToken)

            if (self.__currentInputChar == None):
                self.__reconsumeIn(self.__State.AfterAttributeName)
            elif (charIsWhitespace(self.__currentInputChar)):
                self.__continueIn(self.__State.BeforeAttributeName)
            else:
                self.__currentToken.createNewAttribute()
                self.__reconsumeIn(self.__State.AttributeName)
            

        def handleAttributeName() -> None:
            self.__currentToken = cast(HTMLTag, self.__currentToken)

            if(
                self.__currentInputChar == None or 
                charIsWhitespace(self.__currentInputChar) or
                self.__currentInputChar == "/" or
                self.__currentInputChar == ">"
            ):
                self.__reconsumeIn(self.__State.AfterAttributeName)
            elif(self.__currentInputChar == "="):
                self.__switchTo(self.__State.BeforeAttributeValue)
            elif(self.__currentInputChar.isupper() and self.__currentInputChar.isalpha()):
                self.__currentToken.addCharToAttributeName(self.__currentInputChar.lower())
            else:
                self.__currentToken.addCharToAttributeName(self.__currentInputChar)
                self.__continueIn(self.__State.AttributeName)
            

        def handleAfterAttributeName() -> None:
            return

        def handleBeforeAttributeValue() -> None:
            if (charIsWhitespace(self.__currentInputChar)):
                self.__continueIn(self.__State.BeforeAttributeValue)
            elif (self.__currentInputChar == '"'):
                self.__switchTo(self.__State.AttributeValueDoubleQuoted)
            elif (self.__currentInputChar == "'"):
                self.__switchTo(self.__State.AttributeValueSingleQuoted)
            elif (self.__currentInputChar == ">"):
                self.__emitCurrentToken()
                self.__switchTo(self.__State.Data)
            else:
                self.__reconsumeIn(self.__State.AttributeValueUnquoted)


        def handleAttributeValueDoubleQuoted() -> None:
            self.__currentToken = cast(HTMLTag, self.__currentToken)
            if (self.__currentInputChar == None):
                self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
                self.__emitCurrentToken()
            elif (self.__currentInputChar == '"'):
                self.__switchTo(self.__State.AfterAttributeValueQuoted)
            else:
                self.__currentToken.addCharToAttributeValue(self.__currentInputChar)
                self.__continueIn(self.__State.AttributeValueDoubleQuoted)


        def handleAttributeValueSingleQuoted() -> None:
            self.__currentToken = cast(HTMLTag, self.__currentToken)
            if (self.__currentInputChar == None):
                self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
                self.__emitCurrentToken()
            elif (self.__currentInputChar == "'"):
                self.__switchTo(self.__State.AfterAttributeValueQuoted)
            else:
                self.__currentToken.addCharToAttributeValue(self.__currentInputChar)
                self.__continueIn(self.__State.AttributeValueSingleQuoted)


        def handleAttributeValueUnquoted() -> None:
            self.__currentToken = cast(HTMLTag, self.__currentToken)
            if (self.__currentInputChar == None):
                self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
                self.__emitCurrentToken()
            elif (charIsWhitespace(self.__currentInputChar)):
                self.__switchTo(self.__State.BeforeAttributeName)
            elif (self.__currentInputChar == ">"):
                self.__emitCurrentToken()
                self.__switchTo(self.__State.Data)
            else:
                self.__currentToken.addCharToAttributeValue(self.__currentInputChar)
                self.__continueIn(self.__State.AttributeValueUnquoted)


        def handleAfterAttributeValueQuoted() -> None:
            if (self.__currentInputChar == None):
                self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
                self.__emitCurrentToken()
            elif (charIsWhitespace(self.__currentInputChar)):
                self.__switchTo(self.__State.BeforeAttributeName)
            elif (self.__currentInputChar == "/"):
                self.__switchTo(self.__State.SelfClosingStartTag)
            elif (self.__currentInputChar == ">"):
                self.__emitCurrentToken()
                self.__switchTo(self.__State.Data)
            else:
                self.__reconsumeIn(self.__State.BeforeAttributeName)

        def handleSelfClosingStartTag() -> None:
            return

        def handleBogusComment() -> None:
            return

        def handleMarkupDeclarationOpen() -> None:
            if(self.__nextCharactersAre("--")):
                self.__consumeCharacters("--")
                self.__currentToken = self.__createNewToken(HTMLToken.TokenType.Comment)
                self.__switchTo(self.__State.CommentStart)
            elif (self.__nextCharactersAre("DOCTYPE")):
                self.__consumeCharacters("DOCTYPE")
                self.__switchTo(self.__State.DOCTYPE)

        def handleCommentStart() -> None:

            if (self.__currentInputChar == "-"):
                self.__switchTo(self.__State.CommentStartDash)
            elif(self.__currentInputChar == ">"):
                self.__emitCurrentToken()
                self.__switchTo(self.__State.Data)
            else:
                self.__reconsumeIn(self.__State.Comment)


        def handleCommentStartDash() -> None:
            self.__currentToken = cast(HTMLCommentOrCharacter, self.__currentToken)
            if (self.__currentInputChar == "-"):
                self.__switchTo(self.__State.CommentEnd)
            elif(self.__currentInputChar == ">"):
                self.__emitCurrentToken()
                self.__switchTo(self.__State.Data)
            elif(self.__currentInputChar == None):
                self.__emitCurrentToken()
                self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
                self.__emitCurrentToken()
            else:
                if (self.__currentToken.data != None):
                    self.__currentToken.data += "-"
                else:
                    self.__currentToken.data = "-"
                self.__reconsumeIn(self.__State.Comment)

        def handleComment() -> None:
            self.__currentToken = cast(HTMLCommentOrCharacter, self.__currentToken)
            if (self.__currentInputChar == "-"):
                self.__switchTo(self.__State.CommentEndDash)
            elif(self.__currentInputChar == None):
                self.__emitCurrentToken()
                self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
                self.__emitCurrentToken()
            else:
                if (self.__currentToken.data != None):
                    self.__currentToken.data += self.__currentInputChar
                else:
                    self.__currentToken.data = self.__currentInputChar
                self.__continueIn(self.__State.Comment)

        def handleCommentLessThanSign() -> None:
            return

        def handleCommentLessThanSignBang() -> None:
            return

        def handleCommentLessThanSignBangDash() -> None:
            return

        def handleCommentLessThanSignBangDashDash() -> None:
            return

        def handleCommentEndDash() -> None:
            self.__currentToken = cast(HTMLCommentOrCharacter, self.__currentToken)
            if (self.__currentInputChar == "-"):
                self.__switchTo(self.__State.CommentEnd)
            elif(self.__currentInputChar == None):
                self.__emitCurrentToken()
                self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
                self.__emitCurrentToken()
            else:
                if (self.__currentToken.data != None):
                    self.__currentToken.data += "-"
                else:
                    self.__currentToken.data = "-"
                self.__reconsumeIn(self.__State.Comment)

        def handleCommentEnd() -> None:
            self.__currentToken = cast(HTMLCommentOrCharacter, self.__currentToken)
            if (self.__currentInputChar == ">"):
                self.__emitCurrentToken()
                self.__switchTo(self.__State.Data)
            elif(self.__currentInputChar == "-"):
                if (self.__currentToken.data != None):
                    self.__currentToken.data += "-"
                else:
                    self.__currentToken.data = "-"
                self.__continueIn(self.__State.CommentEnd)
            elif(self.__currentInputChar == None):
                self.__emitCurrentToken()
                self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
                self.__emitCurrentToken()
            else:
                if (self.__currentToken.data != None):
                    self.__currentToken.data += "-"
                else:
                    self.__currentToken.data = "-"
                self.__reconsumeIn(self.__State.Comment)

        def handleCommentEndBang() -> None:
            return

        def handleDOCTYPE() -> None:
            if (charIsWhitespace(cast(str, self.__currentInputChar))):
                self.__switchTo(self.__State.BeforeDOCTYPEName)
            return

        def handleBeforeDOCTYPEName() -> None:
            if (charIsWhitespace(cast(str,self.__currentInputChar))):
                self.__ignoreCharacterAndContinueTo(self.__State.BeforeDOCTYPEName)
            else:
                self.__currentToken = cast(HTMLDoctype, self.__createNewToken(HTMLToken.TokenType.DOCTYPE))
                if (self.__currentToken.name != None and self.__currentInputChar != None):
                    self.__currentToken.name += self.__currentInputChar
                else:
                    self.__currentToken.name = self.__currentInputChar
                
                self.__switchTo(self.__State.DOCTYPEName)
            return

        def handleDOCTYPEName() -> None:
            self.__currentToken = cast(HTMLDoctype, self.__currentToken)
            if (self.__currentInputChar == ">"):
                self.__emitCurrentToken()
                self.__switchTo(self.__State.Data)
            else:
                self.__currentToken.name = self.__currentToken.name + str(self.__currentInputChar)
                self.__continueIn(self.__State.DOCTYPEName)
            return

        def handleAfterDOCTYPEName() -> None:
            return

        def handleAfterDOCTYPEPublicKeyword() -> None:
            return

        def handleBeforeDOCTYPEPublicIdentifier() -> None:
            return

        def handleDOCTYPEPublicIdentifierDoubleQuoted() -> None:
            return

        def handleDOCTYPEPublicIdentifierSingleQuoted() -> None:
            return

        def handleAfterDOCTYPEPublicIdentifier() -> None:
            return

        def handleBetweenDOCTYPEPublicAndSystemIdentifiers() -> None:
            return

        def handleAfterDOCTYPESystemKeyword() -> None:
            return

        def handleBeforeDOCTYPESystemIdentifier() -> None:
            return

        def handleDOCTYPESystemIdentifierDoubleQuoted() -> None:
            return

        def handleDOCTYPESystemIdentifierSingleQuoted() -> None:
            return

        def handleAfterDOCTYPESystemIdentifier() -> None:
            return

        def handleBogusDOCTYPE() -> None:
            return

        def handleCDATASection() -> None:
            return

        def handleCDATASectionBracket() -> None:
            return

        def handleCDATASectionEnd() -> None:
            return

        def handleCharacterReference() -> None:
            return

        def handleNamedCharacterReference() -> None:
            return

        def handleAmbiguousAmpersand() -> None:
            return

        def handleNumericCharacterReference() -> None:
            return

        def handleHexadecimalCharacterReferenceStart() -> None:
            return

        def handleDecimalCharacterReferenceStart() -> None:
            return

        def handleHexadecimalCharacterReference() -> None:
            return

        def handleDecimalCharacterReference() -> None:
            return

        def handleNumericCharacterReferenceEnd() -> None:
            return

        

        switcher = {
            self.__State.Data: handleData,
            self.__State.RCDATA: handleRCDATA,
            self.__State.RAWTEXT: handleRAWTEXT,
            self.__State.ScriptData: handleScriptData,
            self.__State.PLAINTEXT: handlePLAINTEXT,
            self.__State.TagOpen: handleTagOpen,
            self.__State.EndTagOpen: handleEndTagOpen,
            self.__State.TagName: handleTagName,
            self.__State.RCDATALessThanSign: handleRCDATALessThanSign,
            self.__State.RCDATAEndTagOpen: handleRCDATAEndTagOpen,
            self.__State.RCDATAEndTagName: handleRCDATAEndTagName,
            self.__State.RAWTEXTLessThanSign: handleRAWTEXTLessThanSign,
            self.__State.RAWTEXTEndTagOpen: handleRAWTEXTEndTagOpen,
            self.__State.RAWTEXTEndTagName: handleRAWTEXTEndTagName,
            self.__State.ScriptDataLessThanSign: handleScriptDataLessThanSign,
            self.__State.ScriptDataEndTagOpen: handleScriptDataEndTagOpen,
            self.__State.ScriptDataEndTagName: handleScriptDataEndTagName,
            self.__State.ScriptDataEscapeStart: handleScriptDataEscapeStart,
            self.__State.ScriptDataEscapeStartDash: handleScriptDataEscapeStartDash,
            self.__State.ScriptDataEscaped: handleScriptDataEscaped,
            self.__State.ScriptDataEscapedDash: handleScriptDataEscapedDash,
            self.__State.ScriptDataEscapedDashDash: handleScriptDataEscapedDashDash,
            self.__State.ScriptDataEscapedLessThanSign: handleScriptDataEscapedLessThanSign,
            self.__State.ScriptDataEscapedEndTagOpen: handleScriptDataEscapedEndTagOpen,
            self.__State.ScriptDataEscapedEndTagName: handleScriptDataEscapedEndTagName,
            self.__State.ScriptDataDoubleEscapeStart: handleScriptDataDoubleEscapeStart,
            self.__State.ScriptDataDoubleEscaped: handleScriptDataDoubleEscaped,
            self.__State.ScriptDataDoubleEscapedDash: handleScriptDataDoubleEscapedDash,
            self.__State.ScriptDataDoubleEscapedDashDash: handleScriptDataDoubleEscapedDashDash,
            self.__State.ScriptDataDoubleEscapedLessThanSign: handleScriptDataDoubleEscapedLessThanSign,
            self.__State.ScriptDataDoubleEscapeEnd: handleScriptDataDoubleEscapeEnd,
            self.__State.BeforeAttributeName: handleBeforeAttributeName,
            self.__State.AttributeName: handleAttributeName,
            self.__State.AfterAttributeName: handleAfterAttributeName,
            self.__State.BeforeAttributeValue: handleBeforeAttributeValue,
            self.__State.AttributeValueDoubleQuoted: handleAttributeValueDoubleQuoted,
            self.__State.AttributeValueSingleQuoted: handleAttributeValueSingleQuoted,
            self.__State.AttributeValueUnquoted: handleAttributeValueUnquoted,
            self.__State.AfterAttributeValueQuoted: handleAfterAttributeValueQuoted,
            self.__State.SelfClosingStartTag: handleSelfClosingStartTag,
            self.__State.BogusComment: handleBogusComment,
            self.__State.MarkupDeclarationOpen: handleMarkupDeclarationOpen,
            self.__State.CommentStart: handleCommentStart,
            self.__State.CommentStartDash: handleCommentStartDash,
            self.__State.Comment: handleComment,
            self.__State.CommentLessThanSign: handleCommentLessThanSign,
            self.__State.CommentLessThanSignBang: handleCommentLessThanSignBang,
            self.__State.CommentLessThanSignBangDash: handleCommentLessThanSignBangDash,
            self.__State.CommentLessThanSignBangDashDash: handleCommentLessThanSignBangDashDash,
            self.__State.CommentEndDash: handleCommentEndDash,
            self.__State.CommentEnd: handleCommentEnd,
            self.__State.CommentEndBang: handleCommentEndBang,
            self.__State.DOCTYPE: handleDOCTYPE,
            self.__State.BeforeDOCTYPEName: handleBeforeDOCTYPEName,
            self.__State.DOCTYPEName: handleDOCTYPEName,
            self.__State.AfterDOCTYPEName: handleAfterDOCTYPEName,
            self.__State.AfterDOCTYPEPublicKeyword: handleAfterDOCTYPEPublicKeyword,
            self.__State.BeforeDOCTYPEPublicIdentifier: handleBeforeDOCTYPEPublicIdentifier,
            self.__State.DOCTYPEPublicIdentifierDoubleQuoted: handleDOCTYPEPublicIdentifierDoubleQuoted,
            self.__State.DOCTYPEPublicIdentifierSingleQuoted: handleDOCTYPEPublicIdentifierSingleQuoted,
            self.__State.AfterDOCTYPEPublicIdentifier: handleAfterDOCTYPEPublicIdentifier,
            self.__State.BetweenDOCTYPEPublicAndSystemIdentifiers: handleBetweenDOCTYPEPublicAndSystemIdentifiers,
            self.__State.AfterDOCTYPESystemKeyword: handleAfterDOCTYPESystemKeyword,
            self.__State.BeforeDOCTYPESystemIdentifier: handleBeforeDOCTYPESystemIdentifier,
            self.__State.DOCTYPESystemIdentifierDoubleQuoted: handleDOCTYPESystemIdentifierDoubleQuoted,
            self.__State.DOCTYPESystemIdentifierSingleQuoted: handleDOCTYPESystemIdentifierSingleQuoted,
            self.__State.AfterDOCTYPESystemIdentifier: handleAfterDOCTYPESystemIdentifier,
            self.__State.BogusDOCTYPE: handleBogusDOCTYPE,
            self.__State.CDATASection: handleCDATASection,
            self.__State.CDATASectionBracket: handleCDATASectionBracket,
            self.__State.CDATASectionEnd: handleCDATASectionEnd,
            self.__State.CharacterReference: handleCharacterReference,
            self.__State.NamedCharacterReference: handleNamedCharacterReference,
            self.__State.AmbiguousAmpersand: handleAmbiguousAmpersand,
            self.__State.NumericCharacterReference: handleNumericCharacterReference,
            self.__State.HexadecimalCharacterReferenceStart: handleHexadecimalCharacterReferenceStart,
            self.__State.DecimalCharacterReferenceStart: handleDecimalCharacterReferenceStart,
            self.__State.HexadecimalCharacterReference: handleHexadecimalCharacterReference,
            self.__State.DecimalCharacterReference: handleDecimalCharacterReference,
            self.__State.NumericCharacterReferenceEnd: handleNumericCharacterReferenceEnd,
        }
        return switcher.get(self.__state, None)

    def run(self) -> None:
        self.__currentInputChar = self.__nextCodePoint()
        switcher = self.__getStateSwitcher()
        if (switcher != None):
            switcher()
