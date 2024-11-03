from unittest import TestCase
from web.html.parser.HTMLToken import HTMLToken
from web.html.parser.HTMLTokenizerRefactored import HTMLTokenizer


class TestHTMLTokenizer(TestCase):

    def setUp(self):
        pass

    def test_switch_state_to(self):
        tokenizer = HTMLTokenizer()
        self.assertEqual(tokenizer.state, tokenizer.State.Data)
        tokenizer.switch_state_to(tokenizer.State.RCDATA)
        self.assertEqual(tokenizer.state, tokenizer.State.RCDATA)
        
    def test_create_new_token(self):
        current_token: HTMLToken = HTMLTokenizer._create_new_token(HTMLToken.TokenType.Character)
        current_token.data = "a"
        self.assertEqual(current_token.type, HTMLToken.TokenType.Character)
        self.assertEqual(current_token.data, "a")

    def test_parser_whitespace(self):
        for code_point in ["\t", "\n", "\r", "\u000C", " "]:
            current_token = HTMLTokenizer._create_new_token(HTMLToken.TokenType.Character)
            current_token.data = code_point
            self.assertTrue(current_token.is_parser_white_space())

        for code_point in ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]:
            current_token = HTMLTokenizer._create_new_token(HTMLToken.TokenType.Character)
            current_token.data = code_point
            self.assertFalse(current_token.is_parser_white_space())

    def test_data_state_no_input(self):
        tokenizer = HTMLTokenizer()
        self.assertEqual(tokenizer.state, HTMLTokenizer.State.Data)

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.EOF)

        token2 = tokenizer.next_token()
        self.assertEqual(token2, None)
        self.assertEqual(tokenizer.state, HTMLTokenizer.State.Data)

    def test_data_state_single_char(self):
        tokenizer = HTMLTokenizer("X")
        self.assertEqual(tokenizer.state, HTMLTokenizer.State.Data)

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.Character)
        self.assertEqual(token.data, "X")

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.EOF)
        self.assertEqual(tokenizer.state, HTMLTokenizer.State.Data)

        token = tokenizer.next_token()
        self.assertEqual(token, None)

    def test_data_state_ampersand(self):
        tokenizer = HTMLTokenizer("&")
        self.assertEqual(tokenizer.state, HTMLTokenizer.State.Data)

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.Character)
        self.assertEqual(token.data, "&")
        self.assertEqual(tokenizer.state, HTMLTokenizer.State.Data)

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.EOF)
        self.assertEqual(tokenizer.state, HTMLTokenizer.State.Data)

        token = tokenizer.next_token()
        self.assertEqual(token, None)

    def test_tag_open_only(self):
        tokenizer = HTMLTokenizer("<")
        self.assertEqual(tokenizer.state, HTMLTokenizer.State.Data)

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.Character)
        self.assertEqual(token.data, "<")
        self.assertEqual(tokenizer.state, HTMLTokenizer.State.TagOpen)

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.EOF)
        self.assertEqual(tokenizer.state, HTMLTokenizer.State.TagOpen)

        token = tokenizer.next_token()
        self.assertEqual(token, None)

    def test_date_state_null_char(self):
        tokenizer = HTMLTokenizer("H\0I")
        self.assertEqual(tokenizer.state, HTMLTokenizer.State.Data)

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.Character)
        self.assertEqual(token.data, "\uFFFD")

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.Character)
        self.assertEqual(token.data, "\uFFFD")

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.Character)
        self.assertEqual(token.data, "I")

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.EOF)
        self.assertEqual(tokenizer.state, HTMLTokenizer.State.Data)

        token = tokenizer.next_token()
        self.assertEqual(token, None)

    def test_script_tag_with_attributes(self):
        tokenizer = HTMLTokenizer("<script type=\"text/javascript\">")
        self.assertEqual(tokenizer.state, HTMLTokenizer.State.Data)

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.StartTag)
        self.assertEqual(token.name, "script")
        self.assertEqual(token.attributes, {"type": "text/javascript"})

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.EOF)
        self.assertEqual(tokenizer.state, HTMLTokenizer.State.Data)

        token = tokenizer.next_token()
        self.assertEqual(token, None)

    def test_script_tag_with_contents(self):
        tokenizer = HTMLTokenizer("<script>var x = 1;</script>")
        self.assertEqual(tokenizer.state, HTMLTokenizer.State.Data)

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.StartTag)
        self.assertEqual(token.name, "script")
        self.assertEqual(token.attributes, {})

        for code_point in "var x = 1;":
            token = tokenizer.next_token()
            self.assertEqual(token.type, HTMLToken.TokenType.Character)
            self.assertEqual(token.data, code_point)

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.EndTag)
        self.assertEqual(token.name, "script")

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.EOF)
        self.assertEqual(tokenizer.state, HTMLTokenizer.State.Data)

        token = tokenizer.next_token()
        self.assertEqual(token, None)

    def test_simple_div_with_content(self):
        tokenizer = HTMLTokenizer("<div>hi</div>")
        self.assertEqual(tokenizer.state, HTMLTokenizer.State.Data)

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.StartTag)
        self.assertEqual(token.name, "div")
        self.assertEqual(token.attributes, {})

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.Character)
        self.assertEqual(token.data, "h")

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.Character)
        self.assertEqual(token.data, "i")

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.EndTag)
        self.assertEqual(token.name, "div")

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.EOF)
        self.assertEqual(tokenizer.state, HTMLTokenizer.State.Data)

        token = tokenizer.next_token()
        self.assertEqual(token, None)

    def test_simple_div_with_content_and_attributes(self):
        tokenizer = HTMLTokenizer("<div class=\"foo\">hi</div>")
        self.assertEqual(tokenizer.state, HTMLTokenizer.State.Data)

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.StartTag)
        self.assertEqual(token.name, "div")
        self.assertEqual(token.attributes, {"class": "foo"})

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.Character)
        self.assertEqual(token.data, "h")

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.Character)
        self.assertEqual(token.data, "i")

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.EndTag)
        self.assertEqual(token.name, "div")

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.EOF)
        self.assertEqual(tokenizer.state, HTMLTokenizer.State.Data)

        token = tokenizer.next_token()
        self.assertEqual(token, None)

    def test_several_divs_with_attributes_and_content(self):
        tokenizer = HTMLTokenizer("<div class=foo>hi</div><div class='bar'>bye</div>")
        self.assertEqual(tokenizer.state, HTMLTokenizer.State.Data)

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.StartTag)
        self.assertEqual(token.name, "div")
        self.assertEqual(token.attributes, {"class": "foo"})

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.Character)
        self.assertEqual(token.data, "h")

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.Character)
        self.assertEqual(token.data, "i")

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.EndTag)
        self.assertEqual(token.name, "div")

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.StartTag)
        self.assertEqual(token.name, "div")
        self.assertEqual(token.attributes, {"class": "bar"})

        for code_point in "bye":
            token = tokenizer.next_token()
            self.assertEqual(token.type, HTMLToken.TokenType.Character)
            self.assertEqual(token.data, code_point)

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.EndTag)
        self.assertEqual(token.name, "div")

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.EOF)
        self.assertEqual(tokenizer.state, HTMLTokenizer.State.Data)

        token = tokenizer.next_token()
        self.assertEqual(token, None)

    def test_start_tag_with_multiple_attributes(self):
        tokenizer = HTMLTokenizer("<div class=\"foo\" id=\"bar\">hi</div attr=endTagAttribute>")
        self.assertEqual(tokenizer.state, HTMLTokenizer.State.Data)

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.StartTag)
        self.assertEqual(token.name, "div")
        self.assertEqual(token.attributes, {"class": "foo", "id": "bar"})

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.Character)
        self.assertEqual(token.data, "h")

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.Character)
        self.assertEqual(token.data, "i")

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.EndTag)
        self.assertEqual(token.name, "div")
        self.assertEqual(token.attributes, {"attr": "endTagAttribute"})

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.EOF)
        self.assertEqual(tokenizer.state, HTMLTokenizer.State.Data)

        token = tokenizer.next_token()
        self.assertEqual(token, None)

    def test_xml_declaration(self):
        tokenizer = HTMLTokenizer("<?xml version=\"1.0\" encoding=\"UTF-8\"?>")
        self.assertEqual(tokenizer.state, HTMLTokenizer.State.Data)

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.Comment)
        self.assertEqual(token.data, "?xml version=\"1.0\" encoding=\"UTF-8\"?")

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.EOF)
        self.assertEqual(tokenizer.state, HTMLTokenizer.State.Data)

        token = tokenizer.next_token()
        self.assertEqual(token, None)

    def test_simple_comment(self):
        tokenizer = HTMLTokenizer("<!-- comment -->")
        self.assertEqual(tokenizer.state, HTMLTokenizer.State.Data)

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.Comment)
        self.assertEqual(token.data, " comment ")

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.EOF)
        self.assertEqual(tokenizer.state, HTMLTokenizer.State.Data)

        token = tokenizer.next_token()
        self.assertEqual(token, None)

    def test_nested_comment(self):
        tokenizer = HTMLTokenizer("<!-- <!-- nested --> -->")
        self.assertEqual(tokenizer.state, HTMLTokenizer.State.Data)

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.Comment)
        self.assertEqual(token.data, " <!-- nested ")

        for code_point in "bye":
            token = tokenizer.next_token()
            self.assertEqual(token.type, HTMLToken.TokenType.Character)
            self.assertEqual(token.data, code_point)

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.EOF)
        self.assertEqual(tokenizer.state, HTMLTokenizer.State.Data)

        token = tokenizer.next_token()
        self.assertEqual(token, None)

    def test_comment_with_script_tag_inside(self):
        tokenizer = HTMLTokenizer("<!-- <script>var x = 1;</script> -->")
        self.assertEqual(tokenizer.state, HTMLTokenizer.State.Data)

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.Comment)
        self.assertEqual(token.data, " <script>var x = 1;</script> ")

        token = tokenizer.next_token()
        self.assertEqual(token.type, HTMLToken.TokenType.EOF)
        self.assertEqual(tokenizer.state, HTMLTokenizer.State.Data)

        token = tokenizer.next_token()
        self.assertEqual(token, None)