import unittest

from web.js.Value import Value


class TestValue(unittest.TestCase):
    def test_value(self) -> None:

        value_number = Value(1)
        self.assertEqual(value_number.type, Value.Type.Number)
        value_string = Value("test")
        self.assertEqual(value_string.type, Value.Type.String)
        value_boolean = Value(True)
        self.assertEqual(value_boolean.type, Value.Type.Boolean)
        value_null = Value(None)
        self.assertEqual(value_null.type, Value.Type.Null)
        value_undefined = Value(Value)
        self.assertEqual(value_undefined.type, Value.Type.Undefined)

if __name__ == '__main__':
    unittest.main()
