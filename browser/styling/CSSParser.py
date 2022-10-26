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

    def word(self) -> str:
        start = self.index
        while self.index < len(self.style_string):
            if self.style_string[self.index].isalnum() or self.style_string[self.index] in "#-_.%()," or (self.style_string[self.index] == " " and self.style_string[self.index - 1] == ","):
                self.index += 1
            else:
                break
        assert self.index > start
        return self.style_string[start:self.index]

    def literal(self, literal: str) -> None:
        assert self.index < len(
            self.style_string) and self.style_string[self.index] == literal
        self.index += 1

    def pair(self) -> tuple[str, str]:
        prop = self.word()
        self.whitespace()
        self.literal(":")
        self.whitespace()
        val = self.word()
        return prop.lower(), val

    def body(self) -> Dict:
        pairs = {}
        while self.index < len(self.style_string) and self.style_string[self.index] != "}":
            try:
                prop, val = self.pair()
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
        while self.index < len(self.style_string):
            try:
                self.whitespace()
                selector = self.selector()
                self.literal("{")
                self.whitespace()
                body = self.body()
                self.literal("}")
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
        print("Tags: ", tags)
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
