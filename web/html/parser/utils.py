import re


def char_is_whitespace(char: str) -> bool:
    return char.isspace()

def char_is_uppercase_alpha(char: str) -> bool:
    return "A" <= char <= "Z"


def char_is_lowercase_alpha(char: str) -> bool:
    return "a" <= char <= "z"


def char_is_alpha(char: str) -> bool:
    return char_is_lowercase_alpha(char) or char_is_uppercase_alpha(char)


def char_is_surrogate(char: int) -> bool:
    return re.search(r'[\uD800-\uDFFF]', str(char)) is not None


def char_is_noncharacter(char: int) -> bool:
    """
    Try to cast string number to character to determine if it is a character.
    """
    try:
        _ = chr(char)
        return True
    except Exception:
        return False


def char_is_c0_control(char: int) -> bool:
    return char <= 0x1F


def char_is_control(char: int) -> bool:
    return char_is_c0_control(char) or (0x7F <= char <= 0x9F)


def tag_is_special(tagName: str, nameSpace: str = "html") -> bool:
    # Namespace support is still missing so fixed to html.
    if nameSpace == "html":
        return tagName in [
            "address",
            "applet",
            "area",
            "article",
            "aside",
            "base",
            "basefont",
            "bgsound",
            "blockquote",
            "body",
            "br",
            "button",
            "caption",
            "center",
            "col",
            "colgroup",
            "dd",
            "details",
            "dir",
            "div",
            "dl",
            "dt",
            "embed",
            "fieldset",
            "figcaption",
            "figure",
            "footer",
            "form",
            "frame",
            "frameset",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "head",
            "header",
            "hgroup",
            "hr",
            "html",
            "iframe",
            "img",
            "input",
            "keygen",
            "li",
            "link",
            "listing",
            "main",
            "marquee",
            "menu",
            "meta",
            "nav",
            "noembed",
            "noframes",
            "noscript",
            "object",
            "ol",
            "p",
            "param",
            "plaintext",
            "pre",
            "script",
            "section",
            "select",
            "source",
            "style",
            "summary",
            "table",
            "tbody",
            "td",
            "template_",
            "textarea",
            "tfoot",
            "th",
            "thead",
            "title",
            "tr",
            "track",
            "ul",
            "wbr",
            "xmp"
        ]
    elif nameSpace == "svg":
        return tagName in [
            "desc",
            "foreignObject",
            "title"
        ]
    elif nameSpace == "Mathml":
        raise NotImplemented

    return False
