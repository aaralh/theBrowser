from browser.styling.CSSParser import CSSParser
from web.dom.elements.Element import Element
from typing import Dict, List, Optional
from browser.styling.CSSParser import Rule


INHERITED_PROPERTIES = {
    "font-size": "16px",
    "font-style": "normal",
    "font-weight": "normal",
    "color": "black",
}


def cascade_priority(rule: Rule):
    return rule.selector.priority


def computed_style(node: Element, property: str, value: str) -> Optional[str]:
    if property == "font-size":
        if value.endswith("px"):
            return value
        elif value.endswith("%"):
            if node.parentNode:
                parent_font_size = node.parentNode.style["font-size"]
            else:
                parent_font_size = INHERITED_PROPERTIES["font-size"]
                node_pct = float(value[:-1]) / 100
                parent_px = float(parent_font_size[:-2])
                return str(node_pct * parent_px) + "px"
        else:
            return None
    else:
        return value


def get_variable_names(value: str) -> List[str]:
    if "," in value:
        default = value.replace(", ", ",").split(",")[0][4:]
        fallback = value.replace(", ", ",").split(",")[1][4:-2]
        return [default, fallback]
    else:
        return [value[4:-1]]


def get_variable_value(variables: Dict[str, str], variable_names: List[str]):
    for variable_name in variable_names:
        value = variables.get(variable_name)
        if value:
            return value



def style(node: Element, rules: List[Rule]):
    variables: Dict[str, str] = {}

    for rule in rules:
        if not rule.selector.matches(node): continue
        for property, v in rule.body.items():
            if v.is_variable:
                print("found_variable", property, v.value)
                variables[property] = v.value

    node.style = {}
    for property, default_value in INHERITED_PROPERTIES.items():
        if node.parentNode:
            if node.parentNode.style[property] == "inherit":
                node.style[property] = default_value
            else:
                node.style[property] = node.parentNode.style[property]
        else:
            node.style[property] = default_value
    for rule in rules:
        if not rule.selector.matches(node): continue
        print(rule.body)
        for property, value in rule.body.items():
            if value.uses_variable:
                print("Variables: ", variables)
                variable_names = get_variable_names(value.value)
                print("Variable names: ", variable_names)
                val = get_variable_value(variables, variable_names)
                print("Variable value: ", val)
                if val:
                    node.style[property] = val
                    continue


            computed_value = computed_style(node, property, value.value)
            print("no computed_value")
            if not computed_value: continue
            print("computed_value")
            node.style[property] = computed_value
    if isinstance(node, Element) and "style" in node.attributes:
        pairs = CSSParser(node.attributes["style"]).body()
        for property, value in pairs.items():
            computed_value = computed_style(node, property, value.value)
            if not computed_value: continue
            node.style[property] = computed_value
    for child in node.children:
        style(child, rules)
