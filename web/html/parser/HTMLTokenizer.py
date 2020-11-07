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
        self.switchTo(state)


    def __ignoreCharacterAndContinueTo(self, newState: State) -> None:
        self.switchTo(newState)

    def switchTo(self, newState: State) -> None:
        '''
        Switch state and consume next character.
        '''
        self.State = newState
        self.__currentInputChar = self.__nextCodePoint()
        switcher = self.__getStateSwitcher()
        if (switcher != None):
            switcher()

    def __reconsumeIn(self, newState: State) -> None:
        '''
        Switch state without consuming next character.
        '''
        self.State = newState
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
        self.State = self.State.Data
        self.__html = html
        self.__cursor = 0
        self.__currentInputChar: Union[str, None] = None
        self.__returnState: Union[Any, None] = None
        self.__currentToken: Union[HTMLToken, HTMLDoctype, HTMLTag, HTMLCommentOrCharacter, None] = None
        self.__tokenHandlerCb = tokenHandlerCb

    def __getStateSwitcher(self) -> Union[Callable[[], None], None]:

        def handleData() -> None:
            if (self.__currentInputChar == "&"):
                self.__returnState = self.State.Data
                self.switchTo(self.State.CharacterReference)
            elif (self.__currentInputChar == "<"):
                self.switchTo(self.State.TagOpen)
            elif (self.__currentInputChar == None):
                self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
                self.__emitCurrentToken()
                return
            else:
                self.__currentToken = cast(HTMLCommentOrCharacter, self.__createNewToken(HTMLToken.TokenType.Character))
                self.__currentToken.data = self.__currentInputChar
                self.__emitCurrentToken()
                self.__continueIn(self.State.Data)


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
                self.__reconsumeIn(self.State.MarkupDeclarationOpen)
            elif (self.__currentInputChar == "/"):
                self.switchTo(self.State.EndTagOpen)
            elif (self.__currentInputChar.isalpha()):
                self.__currentToken = cast(HTMLTag, self.__createNewToken(HTMLToken.TokenType.StartTag))
                self.__reconsumeIn(self.State.TagName)

        def handleEndTagOpen() -> None:
            self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EndTag)
            self.__reconsumeIn(self.State.TagName)
            return


        def handleTagName() -> None:
            if (self.__currentInputChar == None):
                self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
                self.__emitCurrentToken()
            elif (charIsWhitespace(self.__currentInputChar)):
                self.switchTo(self.State.BeforeAttributeName)
            elif (self.__currentInputChar == ">"):
                self.__emitCurrentToken()
                self.switchTo(self.State.Data)
            else:
                self.__currentToken = cast(HTMLTag, self.__currentToken)
                if (self.__currentToken.name != None and self.__currentInputChar != None):
                    self.__currentToken.name += self.__currentInputChar
                else:
                    self.__currentToken.name = self.__currentInputChar
                self.__continueIn(self.State.TagName)
            

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
                self.__reconsumeIn(self.State.AfterAttributeName)
            elif (charIsWhitespace(self.__currentInputChar)):
                self.__continueIn(self.State.BeforeAttributeName)
            else:
                self.__currentToken.createNewAttribute()
                self.__reconsumeIn(self.State.AttributeName)
            

        def handleAttributeName() -> None:
            self.__currentToken = cast(HTMLTag, self.__currentToken)

            if(
                self.__currentInputChar == None or 
                charIsWhitespace(self.__currentInputChar) or
                self.__currentInputChar == "/" or
                self.__currentInputChar == ">"
            ):
                self.__reconsumeIn(self.State.AfterAttributeName)
            elif(self.__currentInputChar == "="):
                self.switchTo(self.State.BeforeAttributeValue)
            elif(self.__currentInputChar.isupper() and self.__currentInputChar.isalpha()):
                self.__currentToken.addCharToAttributeName(self.__currentInputChar.lower())
            else:
                self.__currentToken.addCharToAttributeName(self.__currentInputChar)
                self.__continueIn(self.State.AttributeName)
            

        def handleAfterAttributeName() -> None:
            return

        def handleBeforeAttributeValue() -> None:
            if (charIsWhitespace(self.__currentInputChar)):
                self.__continueIn(self.State.BeforeAttributeValue)
            elif (self.__currentInputChar == '"'):
                self.switchTo(self.State.AttributeValueDoubleQuoted)
            elif (self.__currentInputChar == "'"):
                self.switchTo(self.State.AttributeValueSingleQuoted)
            elif (self.__currentInputChar == ">"):
                self.__emitCurrentToken()
                self.switchTo(self.State.Data)
            else:
                self.__reconsumeIn(self.State.AttributeValueUnquoted)


        def handleAttributeValueDoubleQuoted() -> None:
            self.__currentToken = cast(HTMLTag, self.__currentToken)
            if (self.__currentInputChar == None):
                self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
                self.__emitCurrentToken()
            elif (self.__currentInputChar == '"'):
                self.switchTo(self.State.AfterAttributeValueQuoted)
            else:
                self.__currentToken.addCharToAttributeValue(self.__currentInputChar)
                self.__continueIn(self.State.AttributeValueDoubleQuoted)


        def handleAttributeValueSingleQuoted() -> None:
            self.__currentToken = cast(HTMLTag, self.__currentToken)
            if (self.__currentInputChar == None):
                self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
                self.__emitCurrentToken()
            elif (self.__currentInputChar == "'"):
                self.switchTo(self.State.AfterAttributeValueQuoted)
            else:
                self.__currentToken.addCharToAttributeValue(self.__currentInputChar)
                self.__continueIn(self.State.AttributeValueSingleQuoted)


        def handleAttributeValueUnquoted() -> None:
            self.__currentToken = cast(HTMLTag, self.__currentToken)
            if (self.__currentInputChar == None):
                self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
                self.__emitCurrentToken()
            elif (charIsWhitespace(self.__currentInputChar)):
                self.switchTo(self.State.BeforeAttributeName)
            elif (self.__currentInputChar == ">"):
                self.__emitCurrentToken()
                self.switchTo(self.State.Data)
            else:
                self.__currentToken.addCharToAttributeValue(self.__currentInputChar)
                self.__continueIn(self.State.AttributeValueUnquoted)


        def handleAfterAttributeValueQuoted() -> None:
            if (self.__currentInputChar == None):
                self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
                self.__emitCurrentToken()
            elif (charIsWhitespace(self.__currentInputChar)):
                self.switchTo(self.State.BeforeAttributeName)
            elif (self.__currentInputChar == "/"):
                self.switchTo(self.State.SelfClosingStartTag)
            elif (self.__currentInputChar == ">"):
                self.__emitCurrentToken()
                self.switchTo(self.State.Data)
            else:
                self.__reconsumeIn(self.State.BeforeAttributeName)

        def handleSelfClosingStartTag() -> None:
            return

        def handleBogusComment() -> None:
            return

        def handleMarkupDeclarationOpen() -> None:
            if(self.__nextCharactersAre("--")):
                self.__consumeCharacters("--")
                self.__currentToken = self.__createNewToken(HTMLToken.TokenType.Comment)
                self.switchTo(self.State.CommentStart)
            elif (self.__nextCharactersAre("DOCTYPE")):
                self.__consumeCharacters("DOCTYPE")
                self.switchTo(self.State.DOCTYPE)

        def handleCommentStart() -> None:

            if (self.__currentInputChar == "-"):
                self.switchTo(self.State.CommentStartDash)
            elif(self.__currentInputChar == ">"):
                self.__emitCurrentToken()
                self.switchTo(self.State.Data)
            else:
                self.__reconsumeIn(self.State.Comment)


        def handleCommentStartDash() -> None:
            self.__currentToken = cast(HTMLCommentOrCharacter, self.__currentToken)
            if (self.__currentInputChar == "-"):
                self.switchTo(self.State.CommentEnd)
            elif(self.__currentInputChar == ">"):
                self.__emitCurrentToken()
                self.switchTo(self.State.Data)
            elif(self.__currentInputChar == None):
                self.__emitCurrentToken()
                self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
                self.__emitCurrentToken()
            else:
                if (self.__currentToken.data != None):
                    self.__currentToken.data += "-"
                else:
                    self.__currentToken.data = "-"
                self.__reconsumeIn(self.State.Comment)

        def handleComment() -> None:
            self.__currentToken = cast(HTMLCommentOrCharacter, self.__currentToken)
            if (self.__currentInputChar == "-"):
                self.switchTo(self.State.CommentEndDash)
            elif(self.__currentInputChar == None):
                self.__emitCurrentToken()
                self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
                self.__emitCurrentToken()
            else:
                if (self.__currentToken.data != None):
                    self.__currentToken.data += self.__currentInputChar
                else:
                    self.__currentToken.data = self.__currentInputChar
                self.__continueIn(self.State.Comment)

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
                self.switchTo(self.State.CommentEnd)
            elif(self.__currentInputChar == None):
                self.__emitCurrentToken()
                self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
                self.__emitCurrentToken()
            else:
                if (self.__currentToken.data != None):
                    self.__currentToken.data += "-"
                else:
                    self.__currentToken.data = "-"
                self.__reconsumeIn(self.State.Comment)

        def handleCommentEnd() -> None:
            self.__currentToken = cast(HTMLCommentOrCharacter, self.__currentToken)
            if (self.__currentInputChar == ">"):
                self.__emitCurrentToken()
                self.switchTo(self.State.Data)
            elif(self.__currentInputChar == "-"):
                if (self.__currentToken.data != None):
                    self.__currentToken.data += "-"
                else:
                    self.__currentToken.data = "-"
                self.__continueIn(self.State.CommentEnd)
            elif(self.__currentInputChar == None):
                self.__emitCurrentToken()
                self.__currentToken = self.__createNewToken(HTMLToken.TokenType.EOF)
                self.__emitCurrentToken()
            else:
                if (self.__currentToken.data != None):
                    self.__currentToken.data += "-"
                else:
                    self.__currentToken.data = "-"
                self.__reconsumeIn(self.State.Comment)

        def handleCommentEndBang() -> None:
            return

        def handleDOCTYPE() -> None:
            if (charIsWhitespace(cast(str, self.__currentInputChar))):
                self.switchTo(self.State.BeforeDOCTYPEName)
            return

        def handleBeforeDOCTYPEName() -> None:
            if (charIsWhitespace(cast(str,self.__currentInputChar))):
                self.__ignoreCharacterAndContinueTo(self.State.BeforeDOCTYPEName)
            else:
                self.__currentToken = cast(HTMLDoctype, self.__createNewToken(HTMLToken.TokenType.DOCTYPE))
                if (self.__currentToken.name != None and self.__currentInputChar != None):
                    self.__currentToken.name += self.__currentInputChar
                else:
                    self.__currentToken.name = self.__currentInputChar
                
                self.switchTo(self.State.DOCTYPEName)
            return

        def handleDOCTYPEName() -> None:
            self.__currentToken = cast(HTMLDoctype, self.__currentToken)
            if (self.__currentInputChar == ">"):
                self.__emitCurrentToken()
                self.switchTo(self.State.Data)
            else:
                self.__currentToken.name = self.__currentToken.name + str(self.__currentInputChar)
                self.__continueIn(self.State.DOCTYPEName)
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
        return switcher.get(self.State, None)

    def run(self) -> None:
        self.__currentInputChar = self.__nextCodePoint()
        switcher = self.__getStateSwitcher()
        if (switcher != None):
            switcher()
