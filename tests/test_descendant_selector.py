import unittest
from web.css.DescendantSelector import DescendantSelector
from web.css.TagSelector import TagSelector
from web.dom.elements.Element import Element
from web.dom.Document import Document
from web.html.parser.HTMLToken import HTMLTag, HTMLToken
from web.dom.Node import Node
from web.dom.events.EventTarget import EventTarget


class MockDocument(Document):
    def __init__(self):
        super().__init__()


class MockNode(Node):
    def __init__(self, parent=None, document=None):
        super().__init__(parent, document or MockDocument())


class MockElement(Element):
    def __init__(self, name: str, attributes=None, parent=None):
        document = MockDocument()
        mock_token = HTMLTag(HTMLToken.TokenType.StartTag)
        mock_token.name = name
        mock_token.attributes = attributes or {}
        parent = parent or MockNode(document=document)
        super().__init__(mock_token, parent, document)
        # Override parentNode set by super().__init__ if a specific parent was provided
        if parent is not None:
            self.parentNode = parent


class TestDescendantSelector(unittest.TestCase):
    def setUp(self):
        # Common selectors used in tests
        self.div_selector = TagSelector("div", [], [])
        self.span_selector = TagSelector("span", [], [])
        self.class_selector = TagSelector("", ["test-class"], [])
        self.id_selector = TagSelector("", [], ["#test-id"])

    def test_initialization(self):
        selector = DescendantSelector(self.div_selector, self.span_selector)
        self.assertEqual(selector.ancestor, self.div_selector)
        self.assertEqual(selector.descendant, self.span_selector)

    def test_priority_calculation(self):
        # Test priority with simple tag selectors
        selector = DescendantSelector(self.div_selector, self.span_selector)
        self.assertEqual(selector.priority, self.div_selector.priority + self.span_selector.priority)

        # Test priority with class selector
        selector = DescendantSelector(self.class_selector, self.span_selector)
        self.assertEqual(selector.priority, self.class_selector.priority + self.span_selector.priority)

        # Test priority with id selector
        selector = DescendantSelector(self.id_selector, self.span_selector)
        self.assertEqual(selector.priority, self.id_selector.priority + self.span_selector.priority)

    def test_matches_direct_parent_child(self):
        # Create a simple parent-child structure
        parent = MockElement("div")
        child = MockElement("span", parent=parent)
        
        selector = DescendantSelector(self.div_selector, self.span_selector)
        
        # Should match when child is span and parent is div
        self.assertTrue(selector.matches(child))
        
        # Should not match when checking against the parent
        self.assertFalse(selector.matches(parent))

    def test_matches_nested_structure(self):
        # Create a nested structure: div > p > span
        grandparent = MockElement("div")
        parent = MockElement("p", parent=grandparent)
        child = MockElement("span", parent=parent)
        
        # Test matching across multiple levels
        selector = DescendantSelector(self.div_selector, self.span_selector)
        self.assertTrue(selector.matches(child))

    def test_matches_with_classes(self):
        # Create a structure with classes
        parent = MockElement("div", {"class": "test-class"})
        child = MockElement("span", parent=parent)
        
        # Test matching with class selector as ancestor
        selector = DescendantSelector(self.class_selector, self.span_selector)
        self.assertTrue(selector.matches(child))

    def test_matches_with_ids(self):
        # Create a structure with IDs
        parent = MockElement("div", {"id": "test-id"})
        child = MockElement("span", parent=parent)
        
        # Test matching with ID selector as ancestor
        selector = DescendantSelector(self.id_selector, self.span_selector)
        self.assertTrue(selector.matches(child))

    def test_no_match_cases(self):
        # Test when there's no parent
        orphan = MockElement("span")
        selector = DescendantSelector(self.div_selector, self.span_selector)
        self.assertFalse(selector.matches(orphan))

        # Test when descendant doesn't match
        parent = MockElement("div")
        wrong_child = MockElement("p", parent=parent)
        self.assertFalse(selector.matches(wrong_child))

        # Test when ancestor doesn't match
        wrong_parent = MockElement("section")
        child = MockElement("span", parent=wrong_parent)
        self.assertFalse(selector.matches(child))

    def test_matches_with_non_element(self):
        # Test with non-Element node
        selector = DescendantSelector(self.div_selector, self.span_selector)
        self.assertFalse(selector.matches(None))
        self.assertFalse(selector.matches("not an element"))

if __name__ == '__main__':
    unittest.main() 