from dataclasses import dataclass
from typing import Any

from web.js.ASTNode import ScopeNode
from web.js.Value import Value


@dataclass
class ScopeFrame:
    scope_node: ScopeNode

class Interpreter:

    def __init__(self):
        pass

    def run(self, scope_node: ScopeNode) -> Any:
        self.__enter_scope(scope_node)
        last_value: Value
        for child in scope_node.children:
            last_value = child.execute(self)

        self.__exit_scope(scope_node)

    def __enter_scope(self, scope_node: ScopeNode):
        raise NotImplementedError

    def __exit_scope(self, scope_node: ScopeNode):
        raise NotImplementedError