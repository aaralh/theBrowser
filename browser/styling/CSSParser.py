from browser.styling.DescendantSelector import DescendantSelector
from browser.styling.TagSelector import TagSelector
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Rule:
    selector: TagSelector
    body: Dict


class CSSParser:
    def __init__(self, style_string: str):
        self.style_string = style_string
        self.index = 0

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
            if current_char.isalnum() or current_char in ",/#-.%()\"'" \
                or (in_quote and current_char == ':'):
                self.index += 1
            else:
                break
        assert self.index > start
        return self.style_string[start:self.index]

    def until_char(self, chars):
        start = self.index
        while self.index < len(self.style_string) and self.style_string[self.index] not in chars:
            self.index += 1
        return self.style_string[start:self.index]

    def pair(self, until) -> tuple[str, str, bool]:
        prop = self.word()
        self.whitespace()
        self.literal(":")
        self.whitespace()
        val = self.until_char(until)
        is_important = val.endswith("!important")
        if is_important:
            val = val.split(" ")[0]
        return prop.lower(), val, is_important

    def body(self) -> Dict:
        pairs = {}
        while self.index < len(self.style_string) and self.style_string[self.index] != "}":
            try:
                prop, val, important  = self.pair([";", "}"])
                pairs[prop.lower()] = val
                self.whitespace()
                self.literal(";")
                self.whitespace()
            except AssertionError as e:
                why = self.ignore_until([";", "}"])
                if why == ";":
                    self.literal(";")
                    self.whitespace()
                else:
                    break
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
        self.whitespace()
        while self.index < len(self.style_string):
            try:
                selector = self.selector()
                self.literal("{")
                self.whitespace()
                body = self.body()
                self.literal("}")
                self.whitespace()
                rules.append(Rule(selector, body))
            except AssertionError:
                why = self.ignore_until(["}"])
                if why == "}":
                    self.literal("}")
                    self.whitespace()
                else:
                    break
        return rules

    def selector(self) -> TagSelector:
        word = self.word().lower()
        classes = list(filter(lambda selector: selector.startswith("."), word.replace(", ", ",").split(",")))
        tags = list(filter(lambda selector: (not selector.startswith(".") and not selector.startswith("#")), word.replace(", ", ",").split(",")))
        ids = list(filter(lambda selector: selector.startswith("#"), word.replace(", ", ",").split(",")))
        tag = next(iter(tags), None)
        out = TagSelector(tag, [cls[1:] for cls in classes], ids)
        self.whitespace()
        while self.index < len(self.style_string) and self.style_string[self.index] != "{":
            word = self.word().lower()
            classes = list(filter(lambda selector: selector.startswith("."), word.replace(", ", ",").split(",")))
            tags = list(filter(lambda selector: (not selector.startswith(".") and not selector.startswith("#")), word.replace(", ", ",").split(",")))
            ids = list(filter(lambda selector: selector.startswith("#"), word.replace(", ", ",").split(",")))
            tag = next(iter(tags), None)
            descendant = TagSelector(tag, [cls[1:] for cls in classes], ids)
            out = DescendantSelector(out, descendant)
            self.whitespace()
        return out
