from browser.styling.CSSParser import CSSParser
from web.dom.elements.Element import Element


def style(node: Element, rules):
    node.style = {}
    for selector, body in rules:
        if not selector.matches(node): continue
        for property, value in body.items():
            node.style[property] = value
    if isinstance(node, Element) and "style" in node.attributes:
        pairs = CSSParser(node.attributes["style"]).body()
        for property, value in pairs.items():
            node.style[property] = value
    for child in node.childNodes:
        style(child, rules)
