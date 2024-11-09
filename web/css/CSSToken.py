from enum import Enum
from typing import Union


class TokenType(Enum):
    """Enum for CSS token types."""
    IDENT = "ident-token"
    FUNCTION = "function-token"
    AT_KEYWORD = "at-keyword-token"
    HASH = "hash-token"
    STRING = "string-token"
    BAD_STRING = "bad-string-token"
    URL = "url-token"
    BAD_URL = "bad-url-token"
    DELIM = "delim-token"
    NUMBER = "number-token"
    PERCENTAGE = "percentage-token"
    DIMENSION = "dimension-token"
    WHITESPACE = "whitespace-token"
    CDO = "CDO-token"
    CDC = "CDC-token"
    COLON = "colon-token"
    SEMICOLON = "semicolon-token"
    COMMA = "comma-token"
    LBRACKET = "[-token"
    RBRACKET = "]-token"
    LPAREN = "(-token"
    RPAREN = ")-token"
    LCURLY = "{-token"
    RCURLY = "}-token"
    EOF = "eof"


class CSSToken:
    """Base class for all CSS token types."""
    def __init__(self, token_type: TokenType):
        if not isinstance(token_type, TokenType):
            raise ValueError(f"Invalid token type: {token_type}")
        self.token_type = token_type

    def __repr__(self):
        return f"CSSToken(type={self.token_type})"


class IdentToken(CSSToken):
    def __init__(self, value: str):
        super().__init__(TokenType.IDENT)
        self.value = value

    def __repr__(self):
        return f"IdentToken(value={self.value})"


class FunctionToken(CSSToken):
    def __init__(self, name: str):
        super().__init__(TokenType.FUNCTION)
        self.name = name

    def __repr__(self):
        return f"FunctionToken(name={self.name})"


class AtKeywordToken(CSSToken):
    def __init__(self, value: str):
        super().__init__(TokenType.AT_KEYWORD)
        self.value = value

    def __repr__(self):
        return f"AtKeywordToken(value={self.value})"


class HashToken(CSSToken):
    class HashType(Enum):
        Unrestricted = "unrestricted"
        Id = "id"


    def __init__(self, value: str):
        super().__init__(TokenType.HASH)
        self.value = value
        self.hash_type: HashToken.HashType = HashToken.HashType.Unrestricted

    def __repr__(self):
        return f"HashToken(value={self.value})"


class StringToken(CSSToken):
    def __init__(self, value: str):
        super().__init__(TokenType.STRING)
        self.value = value

    def __repr__(self):
        return f"StringToken(value={self.value})"


class BadStringToken(CSSToken):
    def __init__(self, value: str):
        super().__init__(TokenType.BAD_STRING)
        self.value = value

    def __repr__(self):
        return f"BadStringToken(value={self.value})"


class UrlToken(CSSToken):
    def __init__(self, value: str):
        super().__init__(TokenType.URL)
        self.value = value

    def __repr__(self):
        return f"UrlToken(value={self.value})"


class BadUrlToken(CSSToken):
    def __init__(self, value: str):
        super().__init__(TokenType.BAD_URL)
        self.value = value

    def __repr__(self):
        return f"BadUrlToken(value={self.value})"


class DelimToken(CSSToken):
    def __init__(self, value: str):
        super().__init__(TokenType.DELIM)
        self.value = value

    def __repr__(self):
        return f"DelimToken(value={self.value})"


class NumberToken(CSSToken):
    def __init__(self, value: float):
        super().__init__(TokenType.NUMBER)
        self.value = value

    def __repr__(self):
        return f"NumberToken(value={self.value})"


class PercentageToken(CSSToken):
    def __init__(self, value: float):
        super().__init__(TokenType.PERCENTAGE)
        self.value = value

    def __repr__(self):
        return f"PercentageToken(value={self.value})"


class DimensionToken(CSSToken):
    def __init__(self, value: float, unit: str, type: Union["number", "integer"]):
        super().__init__(TokenType.DIMENSION)
        self.value = value
        self.unit = unit
        self.type = type

    def __repr__(self):
        return f"DimensionToken(value={self.value}, unit={self.unit})"


class WhitespaceToken(CSSToken):
    def __init__(self):
        super().__init__(TokenType.WHITESPACE)

    def __repr__(self):
        return f"WhitespaceToken()"


class CDO_Token(CSSToken):
    def __init__(self):
        super().__init__(TokenType.CDO)

    def __repr__(self):
        return f"CDO_Token()"


class CDC_Token(CSSToken):
    def __init__(self):
        super().__init__(TokenType.CDC)

    def __repr__(self):
        return f"CDC_Token()"


class ColonToken(CSSToken):
    def __init__(self):
        super().__init__(TokenType.COLON)

    def __repr__(self):
        return f"ColonToken()"


class SemicolonToken(CSSToken):
    def __init__(self):
        super().__init__(TokenType.SEMICOLON)

    def __repr__(self):
        return f"SemicolonToken()"


class CommaToken(CSSToken):
    def __init__(self):
        super().__init__(TokenType.COMMA)

    def __repr__(self):
        return f"CommaToken()"


class LBracketToken(CSSToken):
    def __init__(self):
        super().__init__(TokenType.LBRACKET)

    def __repr__(self):
        return f"LBracketToken()"


class RBracketToken(CSSToken):
    def __init__(self):
        super().__init__(TokenType.RBRACKET)

    def __repr__(self):
        return f"RBracketToken()"


class LParenToken(CSSToken):
    def __init__(self):
        super().__init__(TokenType.LPAREN)

    def __repr__(self):
        return f"LParenToken()"


class RParenToken(CSSToken):
    def __init__(self):
        super().__init__(TokenType.RPAREN)

    def __repr__(self):
        return f"RParenToken()"


class LCurlyToken(CSSToken):
    def __init__(self):
        super().__init__(TokenType.LCURLY)

    def __repr__(self):
        return f"LCurlyToken()"


class RCurlyToken(CSSToken):
    def __init__(self):
        super().__init__(TokenType.RCURLY)

    def __repr__(self):
        return f"RCurlyToken()"

class EOFToken(CSSToken):
    def __init__(self):
        super().__init__(TokenType.EOF)

    def __repr__(self):
        return f"EOFToken()"

