from browser.styling.DescendantSelector import DescendantSelector
from browser.styling.TagSelector import TagSelector
from dataclasses import dataclass
from typing import Dict, List, Optional



@dataclass
class CssPropertyValue:
    value: str
    is_important: bool
    is_variable: bool
    uses_variable: bool


@dataclass
class Rule:
    selector: TagSelector
    body: Dict[str, CssPropertyValue]


class CSSParser:
    def __init__(self, style_string: str):
        self.style_string = style_string
        self.index = 0
        self.in_body = False

    def whitespace(self) -> None:
        while self.index < len(self.style_string) and self.style_string[self.index].isspace():
            self.index += 1

    def literal(self, literal: str) -> None:
        assert self.index < len(
            self.style_string) and self.style_string[self.index] == literal
        self.index += 1

    def word(self) -> str:
        start = self.index
        in_quote = False
        while self.index < len(self.style_string):
            current_char = self.style_string[self.index]
            if current_char == "'":
                in_quote = not in_quote
            if current_char == "(":
                in_parens = True
            if current_char.isalnum() or current_char in ",/#-_.%()\"'" \
                or (in_quote and current_char == ':') \
                or (not self.in_body and current_char == ':'):
                self.index += 1
            else:
                break
        assert self.index > start
        return self.style_string[start:self.index]

    def media_query(self) -> tuple[str, CssPropertyValue]:
        self.literal("@")
        assert self.word() == "media"
        self.whitespace()
        self.literal("(")
        prop, val = self.pair(")")
        self.whitespace()
        self.literal(")")
        return prop, val

    def until_char(self, chars):
        start = self.index
        while self.index < len(self.style_string) and self.style_string[self.index] not in chars:
            self.index += 1
        return self.style_string[start:self.index]

    def pair(self, until) -> tuple[str, CssPropertyValue]:
        prop = self.word()
        self.whitespace()
        self.literal(":")
        self.whitespace()
        val = self.until_char(until)
        is_important = val.endswith("!important")
        is_variable = prop.startswith("--")
        uses_variable = val.startswith("var(")
        if is_important:
            val = val.split("!")[0]
        return prop.lower(), CssPropertyValue(val.strip(), is_important, is_variable, uses_variable)

    def body(self) -> Dict[str, CssPropertyValue]:
        self.in_body = True
        pairs: Dict[str, CssPropertyValue] = {}
        in_comment = False
        while self.index < len(self.style_string) and self.style_string[self.index] != "}":
            try:
                if self.style_string[self.index] == "/" and self.style_string[self.index + 1] == "*":
                    in_comment = True
                    self.literal("/")
                    self.literal("*")
                    self.whitespace()
                    self.ignore_until(["*"])
                elif self.style_string[self.index] == "*" and in_comment:
                    in_comment = False
                    self.literal("*")
                    self.literal("/")
                    self.whitespace()
                prop, val  = self.pair([";", "}"])
                print("style set")
                pairs[prop.lower()] = val
                self.whitespace()
                self.literal(";")
                self.whitespace()
            except AssertionError as e:
                why = self.ignore_until(["*", ";", "}"])
                if why == ";":
                    self.literal(";")
                    self.whitespace()
                elif why == "*":
                    self.literal("*")
                    self.literal("/")
                    self.whitespace()
                else:
                    break

        self.in_body = False
        return pairs

    def ignore_until(self, chars: List[str]) -> Optional[str]:
        while self.index < len(self.style_string):
            if self.style_string[self.index] in chars:
                return self.style_string[self.index]
            else:
                self.index += 1

        return None

    def parse(self) -> List[Rule]:
        rules = []
        media = None
        in_comment = False
        in_root = False
        self.whitespace()
        while self.index < len(self.style_string):
            try:
                if self.style_string[self.index] == "@" and not media:
                    """
                    prop, val = self.media_query()
                    if prop == "prefers-color-scheme" and \
                        val in ["dark", "light"]:
                        media = val
                    """
                    media = "in-media"
                    self.whitespace()
                    self.literal("{")
                    self.whitespace()
                elif self.style_string[self.index] == "}" and media:
                    self.literal("}")
                    media = None
                    self.whitespace()
                elif self.style_string[self.index] == "/" and self.style_string[self.index + 1] == "*":
                    in_comment = True
                    self.literal("/")
                    self.literal("*")
                    self.whitespace()
                    self.ignore_until(["*"])
                elif self.style_string[self.index] == "*" and in_comment:
                    in_comment = False
                    self.literal("*")
                    self.literal("/")
                    self.whitespace()
                else:
                    print("here")
                    selector = self.selector()
                    print("here2")
                    if type(selector) == DescendantSelector:
                        print("Descendant: ", selector.descendant.tag, selector.descendant.classes, selector.descendant.ids)
                    else:
                        print("Selector: ", selector.tag, selector.classes, selector.ids)
                    self.literal("{")
                    self.whitespace()
                    body = self.body()
                    self.literal("}")
                    self.whitespace()
                    if not media and not in_comment:
                        rules.append(Rule(selector, body))
            except AssertionError:
                print("error")
                why = self.ignore_until(["}"])
                if why == "}":
                    self.literal("}")
                    self.whitespace()
                else:
                    break
        return rules

    def split_id_from_selector(self, selector: str) -> tuple[str, Optional[str]]:
        if "#" in selector:
            selector, id = selector.split("#")
            return selector, id
        else:
            return selector, None

    def selector(self) -> TagSelector:
        def get_tags_from_selector(selectors: list[str]) -> list[str]:
            return list(filter(lambda selector: (not selector.startswith(".") and not (selector.startswith("#") or selector.startswith(":"))), selectors))

        word = self.word().lower()
        classes = list(filter(lambda selector: selector.startswith("."), word.replace(", ", ",").split(",")))
        _tags = get_tags_from_selector(word.replace(", ", ",").split(","))
        tags = ([], [])
        pseudo_classes = []

        if ":" in word:
            split = word.split(":")
            pseudo_classes = split[-1:]

        if len(_tags) > 0:
            z = zip
            tags = tuple(map(list, zip(*map(self.split_id_from_selector, _tags))))

        _, _ids = tags
        ids = list(filter(lambda selector: selector.startswith("#"), word.replace(", ", ",").split(",")))
        tag = next(iter(_), "")
        ids = ids + _ids
        out = TagSelector(tag, [cls[1:] for cls in classes], ids, pseudo_classes)
        self.whitespace()
        while self.index < len(self.style_string) and self.style_string[self.index] != "{":
            word = self.word().lower()
            classes = list(filter(lambda selector: selector.startswith("."), word.replace(", ", ",").split(",")))
            _tags = get_tags_from_selector(word.replace(", ", ",").split(","))
            tags = ([], [])
            pseudo_classes = []

            if ":" in word:
                split = word.split(":")
                pseudo_classes = split[-1:]

            if len(_tags) > 0:
                z = zip
                tags = tuple(map(list, zip(*map(self.split_id_from_selector, _tags))))

            _, _ids = tags
            ids = list(filter(lambda selector: selector.startswith("#"), word.replace(", ", ",").split(",")))
            tag = next(iter(_), "")
            ids = ids + _ids
            descendant = TagSelector(tag, [cls[1:] for cls in classes], ids, pseudo_classes)
            out = DescendantSelector(out, descendant)
            self.whitespace()
        return out
