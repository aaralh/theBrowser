import unittest
from web.css.TagSelector import TagSelector
from web.dom.elements.Element import Element
from web.dom.Document import Document
from web.html.parser.HTMLToken import HTMLTag, HTMLToken
from web.dom.Node import Node


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


class TestTagSelector(unittest.TestCase):
    def setUp(self):
        # Common elements used in tests
        self.div_element = MockElement("div")
        self.span_element = MockElement("span")
        self.element_with_class = MockElement("div", {"class": "test-class"})
        self.element_with_multiple_classes = MockElement("div", {"class": "class1 class2"})
        self.element_with_id = MockElement("div", {"id": "test-id"})
        # For tag-plus-class test, we need an element with both tag and class
        self.element_with_tag_and_class = MockElement("div", {"class": "test-class"})
        # For tag-plus-id test, we need an element with both tag and id
        self.element_with_tag_and_id = MockElement("div", {"id": "test-id"})

    def test_initialization(self):
        # Test with tag only
        selector = TagSelector("div", [], [])
        self.assertEqual(selector.tag, "div")
        self.assertEqual(selector.classes, [])
        self.assertEqual(selector.ids, [])
        self.assertEqual(selector.priority, 1)

        # Test with classes
        selector = TagSelector("", ["test-class"], [])
        self.assertEqual(selector.tag, "")
        self.assertEqual(selector.classes, ["test-class"])
        self.assertEqual(selector.ids, [])

        # Test with IDs
        selector = TagSelector("", [], ["#test-id"])
        self.assertEqual(selector.tag, "")
        self.assertEqual(selector.classes, [])
        self.assertEqual(selector.ids, ["#test-id"])

        # Test with all properties
        selector = TagSelector("div", ["test-class"], ["#test-id"])
        self.assertEqual(selector.tag, "div")
        self.assertEqual(selector.classes, ["test-class"])
        self.assertEqual(selector.ids, ["#test-id"])

    def test_matches_tag(self):
        # Test matching by tag name
        selector = TagSelector("div", [], [])
        self.assertTrue(selector.matches(self.div_element))
        self.assertFalse(selector.matches(self.span_element))

    def test_matches_class(self):
        # Test matching by class
        selector = TagSelector("", ["test-class"], [])
        self.assertTrue(selector.matches(self.element_with_class))
        self.assertFalse(selector.matches(self.div_element))

        # Test matching with multiple classes
        selector = TagSelector("", ["class1"], [])
        self.assertTrue(selector.matches(self.element_with_multiple_classes))
        
        selector = TagSelector("", ["class2"], [])
        self.assertTrue(selector.matches(self.element_with_multiple_classes))
        
        selector = TagSelector("", ["nonexistent-class"], [])
        self.assertFalse(selector.matches(self.element_with_multiple_classes))

    def test_matches_id(self):
        # Test matching by ID
        selector = TagSelector("", [], ["#test-id"])
        self.assertTrue(selector.matches(self.element_with_id))
        self.assertFalse(selector.matches(self.div_element))

    def test_matches_tag_plus_class(self):
        # Test matching by tag and class combination
        selector = TagSelector("div.test-class", [], [])
        self.assertTrue(selector.matches(self.element_with_tag_and_class))
        
        # Test with different tag
        selector = TagSelector("span.test-class", [], [])
        self.assertFalse(selector.matches(self.element_with_tag_and_class))
        
        # Test with different class
        selector = TagSelector("div.different-class", [], [])
        self.assertFalse(selector.matches(self.element_with_tag_and_class))

    def test_matches_tag_plus_id(self):
        # Test matching by tag and ID combination
        selector = TagSelector("div", [], ["#test-id"])
        self.assertTrue(selector.matches(self.element_with_tag_and_id))
        
        # Test with different tag
        selector = TagSelector("span", [], ["#test-id"])
        self.assertFalse(selector.matches(self.element_with_tag_and_id))
        
        # Test with different ID
        selector = TagSelector("div", [], ["#different-id"])
        self.assertFalse(selector.matches(self.element_with_tag_and_id))
        
        # Test with no tag but matching ID
        selector = TagSelector("", [], ["#test-id"])
        self.assertTrue(selector.matches(self.element_with_tag_and_id))
        
        # Test with tag but no ID - should match because tag matches
        selector = TagSelector("div", [], [])
        self.assertTrue(selector.matches(self.element_with_tag_and_id))

    def test_matches_without_tag(self):
        # Test matching with only class or ID (no tag)
        selector = TagSelector("", ["test-class"], [])
        self.assertTrue(selector.matches(self.element_with_class))
        
        selector = TagSelector("", [], ["#test-id"])
        self.assertTrue(selector.matches(self.element_with_id))

    def test_matches_with_non_element(self):
        # Test with non-Element node
        selector = TagSelector("div", [], [])
        self.assertFalse(selector.matches(None))
        self.assertFalse(selector.matches("not an element"))

    def test_str_representation(self):
        # Test string representation
        selector = TagSelector("div", ["test-class"], ["#test-id"])
        expected = "Tag: div, class: ['test-class'], ids: ['#test-id']"
        self.assertEqual(str(selector), expected)

        selector = TagSelector("", ["test-class"], [])
        expected = "Tag: , class: ['test-class'], ids: []"
        self.assertEqual(str(selector), expected)

        selector = TagSelector("div", [], [])
        expected = "Tag: div, class: [], ids: []"
        self.assertEqual(str(selector), expected)


if __name__ == '__main__':
    unittest.main() 