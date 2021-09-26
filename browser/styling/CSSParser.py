from browser.styling.DescendantSelector import DescendantSelector
from browser.styling.TagSelector import TagSelector


class CSSParser:
    def __init__(self, style_string: str):
        self.style_string = style_string
        self.index = 0

    def whitespace(self):
        while self.index < len(self.style_string) and self.style_string[self.index].isspace():
            self.index += 1

    def word(self) -> str:
        start = self.index
        while self.index < len(self.style_string):
            if self.style_string[self.index].isalnum() or self.style_string[self.index] in "#-.%":
                self.index += 1
            else:
                break
        assert self.index > start
        return self.style_string[start:self.index]

    def literal(self, literal):
        assert self.index < len(
            self.style_string) and self.style_string[self.index] == literal
        self.index += 1

    def pair(self):
        prop = self.word()
        self.whitespace()
        self.literal(":")
        self.whitespace()
        val = self.word()
        return prop.lower(), val

    def body(self):
        pairs = {}
        while self.index < len(self.style_string) and self.style_string[self.index] != "}":
            try:
                prop, val = self.pair()
                pairs[prop.lower()] = val
                self.whitespace()
                self.literal(";")
                self.whitespace()
            except AssertionError:
                why = self.ignore_until([";", "}"])
                if why == ";":
                    self.literal(";")
                    self.whitespace()
                else:
                    break
        return pairs

    def ignore_until(self, chars):
        while self.index < len(self.style_string):
            if self.style_string[self.index] in chars:
                return self.style_string[self.index]
            else:
                self.index += 1

    def parse(self):
        rules = []
        while self.index < len(self.style_string):
            try:
                self.whitespace()
                selector = self.selector()
                self.literal("{")
                self.whitespace()
                body = self.body()
                self.literal("}")
                rules.append((selector, body))
            except AssertionError:
                why = self.ignore_until(["}"])
                if why == "}":
                    self.literal("}")
                    self.whitespace()
                else:
                    break
        return rules

    def selector(self):
        out = TagSelector(self.word().lower())
        self.whitespace()
        while self.index < len(self.style_string) and self.style_string[self.index] != "{":
            tag = self.word()
            descendant = TagSelector(tag.lower())
            out = DescendantSelector(out, descendant)
            self.whitespace()
        return out