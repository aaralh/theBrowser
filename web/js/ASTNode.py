import enum
from typing import List
from abc import ABC, abstractmethod


from web.js.Interpreter import Interpreter
from web.js.Value import Value


class ASTNode(ABC):

    def __init__(self):
        pass

    @abstractmethod
    def execute(self, interpreter: Interpreter) -> Value:
        raise NotImplementedError


class ScopeNode(ABC, ASTNode):

    def __init__(self):
        self.__children: List[ASTNode] = []


    @property
    def children(self) -> List[ASTNode]:
        return self.__children

    def append_child(self, child: ASTNode):
        self.__children.append(child)
        return self.__children[-1]


class Program(ScopeNode):

    def __init__(self, name: str):
        self.__name = name
        self.__children: List[ASTNode] = []

    @property
    def name(self) -> str:
        return self.__name

    @property
    def children(self) -> List[ASTNode]:
        return self.__children

    def append_child(self, child: ASTNode):
        self.__children.append(child)
        return self.__children[-1]


class BlockStatement(ScopeNode):

    def __init__(self):
        pass


class Expression(ASTNode):

    def __init__(self):
        pass


class ReturnStatement(ASTNode):

    def __init__(self, argument: Expression):
        self.__argument: Expression = argument

    @property
    def argument(self) -> Expression:
        return self.__argument

    @argument.setter
    def argument(self, argument: Expression) -> None:
        self.__argument = argument


class BinaryOperator(enum.Enum):
    Plus = enum.auto()
    Minus = enum.auto()


class BinaryExpression(Expression):

    def __init__(
            self,
            binary_operator: BinaryOperator,
            left_hand_side: Expression,
            right_hand_side: Expression):
        self.__binary_operator = binary_operator
        self.__left_hand_side = left_hand_side
        self.__right_hand_side = right_hand_side


    def execute(self) -> Value:
        raise NotImplementedError


class Literal(Expression):

    def __init__(self, value: Value):
        self.__value  = value

    def execute(self) -> Value:
        return self.__value

class ExpressionStatement(ASTNode):

    def __init__(self):
        pass


class CallExpression(Expression):

    def __init__(self):
        pass


class FunctionDeclaration(ASTNode):

    def __init__(self, name: str, body: ScopeNode):
        self.__name = name
        self.__body: ScopeNode = body

    @property
    def name(self) -> str:
        return self.__name

    @property
    def body(self) -> ScopeNode:
        return self.__body

