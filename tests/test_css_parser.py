import unittest
from web.css.CSSParser import CSSParser, Rule
from web.css.TagSelector import TagSelector
from web.css.DescendantSelector import DescendantSelector

class TestCSSParser(unittest.TestCase):
    def test_whitespace(self):
        parser = CSSParser("   test")
        parser.whitespace()
        self.assertEqual(parser.index, 3)

    def test_literal(self):
        parser = CSSParser("test")
        parser.literal("t")
        self.assertEqual(parser.index, 1)
        with self.assertRaises(AssertionError):
            parser.literal("x")

    def test_word(self):
        parser = CSSParser("test-word")
        self.assertEqual(parser.word(), "test-word")
        
        parser = CSSParser("test.word")
        self.assertEqual(parser.word(), "test.word")
        
        parser = CSSParser("test#id")
        self.assertEqual(parser.word(), "test#id")

    def test_media_query(self):
        parser = CSSParser("@media (max-width: 800px)")
        prop, val = parser.media_query()
        self.assertEqual(prop, "max-width")
        self.assertEqual(val, "800px")

    def test_until_char(self):
        parser = CSSParser("test;end")
        result = parser.until_char([";"])
        self.assertEqual(result, "test")

    def test_pair(self):
        parser = CSSParser("color: red;")
        prop, val, important = parser.pair([";"])
        self.assertEqual(prop, "color")
        self.assertEqual(val, "red")
        self.assertFalse(important)

        parser = CSSParser("color: red !important;")
        prop, val, important = parser.pair([";"])
        self.assertEqual(prop, "color")
        self.assertEqual(val, "red")
        self.assertTrue(important)

    def test_body(self):
        parser = CSSParser("color: red; background: blue;")
        pairs = parser.body()
        self.assertEqual(pairs, {"color": "red", "background": "blue"})

        # Test with comments
        parser = CSSParser("/* comment */ color: red; /* another comment */ background: blue;")
        pairs = parser.body()
        self.assertEqual(pairs, {"color": "red", "background": "blue"})

    def test_ignore_until(self):
        parser = CSSParser("test;end")
        result = parser.ignore_until([";"])
        self.assertEqual(result, ";")

    def test_split_id_from_selector(self):
        parser = CSSParser("")
        selector, id = parser.split_id_from_selector("div#test")
        self.assertEqual(selector, "div")
        self.assertEqual(id, "test")

        selector, id = parser.split_id_from_selector("div")
        self.assertEqual(selector, "div")
        self.assertIsNone(id)

    def test_selector(self):
        # Test simple tag selector
        parser = CSSParser("div {")
        selector = parser.selector()
        self.assertIsInstance(selector, TagSelector)
        self.assertEqual(selector.tag, "div")
        self.assertEqual(selector.classes, [])
        self.assertEqual([id for id in selector.ids if id is not None], [])  # Filter out None values

        # Test class selector
        parser = CSSParser(".class {")
        selector = parser.selector()
        self.assertEqual(selector.tag, "")
        self.assertEqual(selector.classes, ["class"])
        self.assertEqual([id for id in selector.ids if id is not None], [])

        # Test ID selector
        parser = CSSParser("#id {")
        selector = parser.selector()
        self.assertEqual(selector.tag, "")
        self.assertEqual(selector.ids, ["#id"])  # IDs include the '#' prefix as expected by TagSelector

        # Test descendant selector
        parser = CSSParser("div span {")
        selector = parser.selector()
        self.assertIsInstance(selector, DescendantSelector)
        self.assertEqual(selector.ancestor.tag, "div")
        self.assertEqual(selector.descendant.tag, "span")
        self.assertEqual([id for id in selector.ancestor.ids if id is not None], [])
        self.assertEqual([id for id in selector.descendant.ids if id is not None], [])

    def test_parse(self):
        # Test simple rule
        css = "div { color: red; }"
        parser = CSSParser(css)
        rules = parser.parse()
        self.assertEqual(len(rules), 1)
        self.assertIsInstance(rules[0], Rule)
        self.assertEqual(rules[0].body, {"color": "red"})

        # Test multiple rules
        css = """
        div { color: red; }
        span { background: blue; }
        """
        parser = CSSParser(css)
        rules = parser.parse()
        self.assertEqual(len(rules), 2)

        # Test with media query
        css = """
        @media (max-width: 800px) {
            div { color: red; }
        }
        """
        parser = CSSParser(css)
        rules = parser.parse()
        self.assertEqual(len(rules), 0)  # Rules inside media queries are ignored

        # Test with comments
        css = """
        /* comment */
        div { color: red; }
        /* another comment */
        span { background: blue; }
        """
        parser = CSSParser(css)
        rules = parser.parse()
        self.assertEqual(len(rules), 2)

if __name__ == '__main__':
    unittest.main() 