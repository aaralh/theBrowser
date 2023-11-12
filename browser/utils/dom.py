from typing import List
from web.dom.Node import Node

def tree_to_list(node: Node, list: List) -> List[Node]:
    list.append(node)
    for child in node.children:
        tree_to_list(child, list)
    return list
