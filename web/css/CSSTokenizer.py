from dataclasses import dataclass
from typing import Optional, Union, Literal, Tuple

from web.css.CSSToken import CSSToken, PercentageToken, WhitespaceToken, StringToken, BadStringToken, DelimToken, \
    HashToken, \
    NumberToken, LParenToken, RParenToken, DimensionToken, EOFToken, CommaToken, LCurlyToken, RCurlyToken, \
    LBracketToken, RBracketToken, SemicolonToken, ColonToken, CDC_Token, IdentToken, FunctionToken, UrlToken, \
    BadUrlToken, CDO_Token, AtKeywordToken


def is_whitespace(char: str) -> bool:
    if len(char) != 1:
        raise ValueError("Input must be a single character.")

    if char is None:
        return False

    return char in {'\n', '\t', ' '}

def is_newline(char: str) -> bool:
    return char in {'\n', '\r\n'}


def is_hex_digit(char: str) -> bool:
    if len(char) != 1:
        raise ValueError("Input must be a single character.")

    return char in '0123456789abcdefABCDEF'

def is_non_printable(char):
    # Get the Unicode code point of the character
    code_point = ord(char)

    # Check if the code point is in any of the non-printable ranges
    if (0x0000 <= code_point <= 0x0008) or (code_point == 0x000B) or (0x000E <= code_point <= 0x001F) or (code_point == 0x007F):
        return True
    return False


# 4.3.13 https://www.w3.org/TR/css-syntax-3/#convert-a-string-to-a-number
def convert_to_number(number_string: str):
    # Step 1: Initialize components
    sign_multiplier = 1  # Default sign is positive
    integer_part = 0  # Default integer part is 0
    fractional_part = 0  # Default fractional part is 0
    fractional_digits_count = 0  # Default number of fractional digits is 0
    exponent_sign_multiplier = 1  # Default exponent sign is positive
    exponent_value = 0  # Default exponent is 0

    # Step 2: Process the sign
    if number_string.startswith('-'):
        sign_multiplier = -1
        number_string = number_string[1:]  # Remove the sign character
    elif number_string.startswith('+'):
        number_string = number_string[1:]  # Remove the sign character

    # Step 3: Process the integer part
    integer_part_str = ''
    while number_string and number_string[0].isdigit():
        integer_part_str += number_string[0]
        number_string = number_string[1:]

    if integer_part_str:
        integer_part = int(integer_part_str)

    # Step 4: Process the decimal point and fractional part
    if number_string.startswith('.'):
        number_string = number_string[1:]  # Skip the decimal point
        fractional_part_str = ''
        while number_string and number_string[0].isdigit():
            fractional_part_str += number_string[0]
            number_string = number_string[1:]
        if fractional_part_str:
            fractional_part = int(fractional_part_str)
            fractional_digits_count = len(fractional_part_str)

    # Step 5: Process the exponent part (e or E)
    if number_string.lower().startswith('e'):
        number_string = number_string[1:]  # Skip the 'e' or 'E'

        if number_string.startswith('-'):
            exponent_sign_multiplier = -1
            number_string = number_string[1:]
        elif number_string.startswith('+'):
            number_string = number_string[1:]

        exponent_digits_str = ''
        while number_string and number_string[0].isdigit():
            exponent_digits_str += number_string[0]
            number_string = number_string[1:]
        if exponent_digits_str:
            exponent_value = int(exponent_digits_str)

    # Step 6: Compute the final number
    final_value = sign_multiplier * (integer_part + fractional_part * 10 ** (-fractional_digits_count)) * 10 ** (
                exponent_sign_multiplier * exponent_value)
    return final_value


# https://www.w3.org/TR/css-syntax-3/#ident-code-point
def is_ident_start(char: str) -> bool:
    if len(char) != 1:
        raise ValueError("Input must be a single character.")

    # Check if the character is:
    # - a Unicode letter (uppercase or lowercase)
    # - underscore (_) or hyphen-minus (-)
    return char.isalpha() or char == '_' or char == '-'

def is_ident(char: str) -> bool:
    return is_ident_start(char) or char.isdigit() or char == "-"


def is_escape_sequence_valid(first: str, second: str) -> bool:
    """Checks if two code points form a valid escape sequence (e.g., \ followed by a valid hex or non-whitespace character)."""
    if first == '\\':
        # We can check if the second code point is a valid escape (e.g., a hex digit, letter, or other valid escape)
        return second.isalnum() or second == '\n'  # For simplicity, assuming escape is followed by alphanumeric or newline
    return False

# 4.3.8 https://www.w3.org/TR/css-syntax-3/#starts-with-a-valid-escape
def is_valid_escape(first: str, second: str) -> bool:
    return first == "\\" and not is_newline(second)

# 4.3.9 https://www.w3.org/TR/css-syntax-3/#would-start-an-identifier
def is_starting_ident_sequence(code1: str, code2: str, code3: str) -> bool:
    # Check for first code point being a hyphen-minus
    if code1 == '-':
        if is_ident_start(code2) or code2 == '-' or is_escape_sequence_valid(code2, code3):
            return True
        return False

    if is_ident_start(code1):
        return True

    if code1 == '\\':
        if is_escape_sequence_valid(code1, code2):
            return True
        return False

    return False


class CSSTokenizer:

    def __init__(self, css_string: str):
        self.css_string = css_string
        self.css_string_length = len(css_string)
        self.current_code_point: Optional[str] = None
        self.current_cursor_position = -1

    def reconsume_current_code_point(self):
        self.current_cursor_position -= 1

    def consume_next_code_point(self):
        self.current_code_point = self.get_next_code_point()

    def get_next_code_point(self) -> Optional[str]:
        self.current_cursor_position += 1
        if self.current_cursor_position >= self.css_string_length:
            return None

        return self.preprocess_code_point(self.css_string[self.current_cursor_position])

    def peek_code_point(self, delta: int):
        if self.current_cursor_position + delta >= self.css_string_length:
            return None

        return self.preprocess_code_point(self.css_string[self.current_cursor_position + delta])

    # 3.3 https://www.w3.org/TR/css-syntax-3/#input-preprocessing
    @staticmethod
    def preprocess_code_point(code_point: Optional[str]):
        if not code_point:
            return code_point

        # Ensure input is a single character
        if len(code_point) != 1:
            raise ValueError("Input must be a single character.")

        # Replace CR, FF, or CRLF with LF
        if code_point == '\r' or code_point == '\f':
            return '\n'

        # Replace NULL or surrogate code points with U+FFFD
        unicode_code_point = ord(code_point)
        if unicode_code_point == 0x0000 or 0xD800 <= unicode_code_point <= 0xDFFF:
            return '\uFFFD'

        # Return the character unchanged if no replacement was needed
        return code_point

    def consume_comment(self):
        while True:
            self.consume_next_code_point()
            if self.current_code_point == "/" and self.peek_code_point(-1) == "*":
                break
            elif self.current_code_point is None:
                # TODO: Handle parse error.
                break

    def consume_whitespace(self):
        while is_whitespace(self.peek_code_point(1)):
            self.consume_next_code_point()
            if self.peek_code_point(1) is None:
                break
        return WhitespaceToken()

    # 4.3.7 https://www.w3.org/TR/css-syntax-3/#consume-escaped-code-point
    def consume_escaped_code_point(self) -> str:
        MAX_CODE_POINT = 0x10FFFF
        surrogate_start = 0xD800
        surrogate_end = 0xDFFF
        self.consume_next_code_point()
        if self.current_code_point is None:
            return '\uFFFD'
        elif is_hex_digit(self.current_code_point):
            hex_digits_consumed = [self.current_code_point]
            for _ in range(5):
                self.consume_next_code_point()
                if is_hex_digit(self.current_code_point):
                    hex_digits_consumed.append(self.current_code_point)
                    continue
                if self.current_code_point is None:
                    return '\uFFFD'
                break

            if is_whitespace(self.current_code_point):
                self.consume_next_code_point()

            if hex_digits_consumed:
                hex_value = int(''.join(hex_digits_consumed), 16)

                # Step 3: Check for invalid code points
                if hex_value == 0 or hex_value > MAX_CODE_POINT or surrogate_start <= hex_value <= surrogate_end:
                    return '\uFFFD'  # Invalid code point, return replacement character
                else:
                    return chr(hex_value)  # Valid code point
            else:
                # Step 4: If no hex digits were consumed, return the current character
                return self.current_code_point if 'char' in locals() else '\uFFFD'  # Handle EOF
        else:
            return self.current_code_point


    # 4.3.5 https://www.w3.org/TR/css-syntax-3/#consume-string-token
    def consume_string_token(self, ending_code_point: str = None) -> Union[StringToken, BadStringToken]:
        token = StringToken("")

        while True:
            self.consume_next_code_point()
            if ending_code_point is not None and self.current_code_point == ending_code_point:
                return token
            elif self.current_code_point is None:
                return token
            elif is_newline(self.current_code_point):
                self.reconsume_current_code_point()
                return token
            elif self.current_code_point == "\\":
                next_token = self.peek_code_point(1)
                if next_token is None:
                    continue
                elif is_newline(next_token):
                    token.value += self.consume_next_code_point()
                else:
                    self.consume_escaped_code_point()
            else:
                token.value += self.current_code_point

    # 4.3.11 https://www.w3.org/TR/css-syntax-3/#consume-name
    def consume_ident_sequence(self):
        result = ""
        while True:
            if is_ident(self.current_code_point):
                result += self.current_code_point
                self.consume_next_code_point()
            elif is_valid_escape(self.current_code_point, self.peek_code_point(1)):
                result += self.consume_escaped_code_point()
            else:
                self.reconsume_current_code_point()
                return result

    # 4.3.14 https://www.w3.org/TR/css-syntax-3/#consume-the-remnants-of-a-bad-url
    def consume_remnants_of_a_bad_url(self):
        while True:
            self.consume_next_code_point()
            if self.current_code_point is None or self.current_code_point == ")":
                break
            elif is_valid_escape(self.current_code_point, self.peek_code_point(1)):
                self.consume_escaped_code_point()
            else:
                continue

    # 4.3.6 https://www.w3.org/TR/css-syntax-3/#consume-a-url-token
    def consume_url_token(self):
        token = UrlToken("")
        while is_whitespace(self.peek_code_point(1)):
            self.consume_next_code_point()

        while True:
            self.consume_next_code_point()
            if self.current_code_point is None:
                return token
            elif self.current_code_point == ")":
                return token
            elif is_whitespace(self.current_code_point):
                while is_whitespace(self.peek_code_point(1)):
                    self.consume_next_code_point()
            elif self.current_code_point in ['"', "'", "("] or is_non_printable(self.current_code_point):
                self.consume_remnants_of_a_bad_url()
                return BadUrlToken("")
            elif self.current_code_point == "\\":
                if is_valid_escape(self.current_code_point, self.peek_code_point(1)):
                    token.value += self.consume_escaped_code_point()
                else:
                    self.consume_remnants_of_a_bad_url()
                    return BadUrlToken("")
            else:
                token.value += self.current_code_point


    # 4.3.4 https://www.w3.org/TR/css-syntax-3/#consume-an-ident-like-token
    def consume_ident_like_token(self) -> Union[IdentToken, FunctionToken, UrlToken, BadUrlToken]:
        result = self.consume_ident_sequence()

        if result.lower() == "url" and self.peek_code_point(1) == "(":
            self.consume_next_code_point()
            while is_whitespace(self.peek_code_point(1)):
                self.consume_next_code_point()

            if self.peek_code_point(1) in ['"', "'"] or (is_whitespace(self.peek_code_point(1) and self.peek_code_point(2) in ['"', "'"])) or \
                    (self.peek_code_point(1) in ['"', "'"] or (is_whitespace(self.peek_code_point(1) and self.peek_code_point(2) in ['"', "'"])) and
                            self.peek_code_point(2) in ['"', "'"] or (is_whitespace(self.peek_code_point(2) and self.peek_code_point(3) in ['"', "'"]))):

                return FunctionToken(result)
            elif self.peek_code_point(1) == "(":
                self.consume_next_code_point()
                return FunctionToken(result)
            else:
                return self.consume_url_token()
        else:
            return IdentToken(result)


    def consume_number(self) -> Tuple[Union[int, float], Union["integer", "number"]]:
        number_str = ''
        number_type: Union[Literal["integer"], Literal["number"]] = "integer"
        if self.current_code_point in ["+", "-"]:
            number_str += self.current_code_point
        while True:
            self.current_code_point = self.get_next_code_point()
            if self.current_code_point.isdigit():
                number_str += self.current_code_point
            elif self.current_code_point == "." and self.peek_code_point(1).isdigit():
                number_str += self.current_code_point
                self.current_code_point = self.get_next_code_point()
                number_str += self.current_code_point
            elif self.current_code_point in ["E", "e"]:
                if self.peek_code_point(1).isdigit():
                    number_str += self.current_code_point
                    self.current_code_point = self.get_next_code_point()
                    number_str += self.current_code_point
                    number_type = "number"
                elif self.peek_code_point(1) in ["+", "-"] and self.peek_code_point(2).isdigit():
                    number_str += self.current_code_point
                    self.current_code_point = self.get_next_code_point()
                    number_str += self.current_code_point
                    self.current_code_point = self.get_next_code_point()
                    number_str += self.current_code_point
                    number_type = "number"
            else:
                break

        number = convert_to_number(number_str)

        return number, number_type

    # 4.3.3 https://www.w3.org/TR/css-syntax-3/#consume-numeric-token
    def consume_numeric_token(self):
        number, number_type = self.consume_number()

        if is_starting_ident_sequence(self.current_code_point, self.peek_code_point(1), self.peek_code_point(2)):
            token = DimensionToken(number, "", number_type)
            token.unit += self.current_code_point
            self.consume_next_code_point()
            token.unit += self.current_code_point
            self.consume_next_code_point()
            token.unit += self.current_code_point
            return token

        if self.current_code_point == '%':
            self.consume_next_code_point()
            return PercentageToken(number)

        return NumberToken(number)

    # 4.3.1 https://www.w3.org/TR/css-syntax-3/#consume-token
    def next_token(self) -> CSSToken:
        while True:
            self.consume_next_code_point()
            if self.current_code_point is None:
                return EOFToken()
            elif self.current_code_point == "/" and self.peek_code_point(1) == "*":
                self.consume_comment()
            elif is_whitespace(self.current_code_point):
                return self.consume_whitespace()
            elif self.current_code_point == '"':
                return self.consume_string_token()
            elif self.current_code_point == "#":
                if is_ident_start(self.current_code_point) or \
                        is_valid_escape(self.current_code_point , self.peek_code_point(1)):
                    token = HashToken("")
                    if is_starting_ident_sequence(self.current_code_point, self.peek_code_point(1), self.peek_code_point(2)):
                        token.hash_type = HashToken.HashType.Id
                    token.value = self.consume_ident_sequence()
                    return token
                else:
                    return DelimToken(self.current_code_point)
            elif self.current_code_point == "'":
                return self.consume_string_token()
            elif self.current_code_point == "(":
                return LParenToken()
            elif self.current_code_point == ")":
                return RParenToken()
            elif self.current_code_point == "+":
                if self.peek_code_point(1).isdigit():
                    self.consume_next_code_point()
                    return self.consume_numeric_token()
                else:
                    return DelimToken(self.current_code_point)
            elif self.current_code_point == ",":
                return CommaToken()
            elif self.current_code_point == "-":
                if self.peek_code_point(1).isdigit():
                    self.consume_next_code_point()
                    return self.consume_numeric_token()
                elif self.peek_code_point(1) == "-" and self.peek_code_point(2) == ">":
                    self.consume_next_code_point()
                    self.consume_next_code_point()
                    return CDC_Token()
                elif is_starting_ident_sequence(self.current_code_point, self.peek_code_point(1), self.peek_code_point(2)):
                    return self.consume_ident_like_token()
                else:
                    return DelimToken(self.current_code_point)

            elif self.current_code_point == ".":
                if self.peek_code_point(1).isdigit():
                    return self.consume_numeric_token()
                else:
                    return DelimToken(self.current_code_point)
            elif self.current_code_point == ":":
                return ColonToken()
            elif self.current_code_point == ";":
                return SemicolonToken()
            elif self.current_code_point == "<":
                if [self.peek_code_point(1), self.peek_code_point(2), self.peek_code_point(3)] == ["!", "-", "-"]:
                    self.consume_next_code_point()
                    self.consume_next_code_point()
                    self.consume_next_code_point()
                    return CDO_Token()
                else:
                    return DelimToken(self.current_code_point)
            elif self.current_code_point == "@":
                if is_starting_ident_sequence(self.current_code_point, self.peek_code_point(1), self.peek_code_point(2)):
                    result = self.consume_ident_sequence()
                    return AtKeywordToken(result)
                else:
                    return DelimToken(self.current_code_point)
            elif self.current_code_point == "[":
                return LBracketToken()
            elif self.current_code_point == "\\":
                if is_valid_escape(self.current_code_point, self.peek_code_point(1)):
                    return self.consume_ident_like_token()
                else:
                    return DelimToken(self.current_code_point)
            elif self.current_code_point == "]":
                return RBracketToken()
            elif self.current_code_point == "{":
                return LCurlyToken()
            elif self.current_code_point == "}":
                return RCurlyToken()
            elif self.current_code_point.isdigit():
                return self.consume_numeric_token()
            else:
                return DelimToken(self.current_code_point)