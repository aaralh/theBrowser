import unittest

from web.js.ASTNode import *


class TestASTNode(unittest.TestCase):
    def test_ASTNode(self) -> None:

        program = Program()

        block = BlockStatement()
        return_statement = ReturnStatement(BinaryExpression(
            BinaryOperator.Plus,
            Literal(Value(1)),
            Literal(Value(2))
        ))
        block.append_child(return_statement)
        function_declaration = FunctionDeclaration("foo", block)

        program.append_child(function_declaration)
        program.append_child(ExpressionStatement(CallExpression("foo")))
        self.assertEqual(value_undefined.type, Value.Type.Undefined)

if __name__ == '__main__':
    unittest.main()
