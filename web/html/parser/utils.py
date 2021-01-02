import re

def charIsWhitespace(char: str) -> bool:
	whitespaces = ["\t", "\a", "\f", " "]
	return char in whitespaces

def charIsUppercaseAlpha(char: str) -> bool:
	return char >= "A" and char <= "Z"

def charIsLowercaseAlpha(char: str) -> bool:
	return char >= "a" and char <= "z"

def charIsAlpha(char: str) -> bool:
	return charIsLowercaseAlpha(char) or charIsUppercaseAlpha(char)

def charIsSurrogate(char: int) -> bool:
	return re.search(r'[\uD800-\uDFFF]', str(char)) is not None

def charIsNoncharacter(char: int) -> bool:
	"""
	Try to cast string number to character to determine if it is a character.
	"""
	try:
		_ = chr(char)
		return True
	except Exception as e:
		return False

def charIsC0Control(char: int) -> bool:
	return char <= 0x1F

def charIsControl(char: int) -> bool:
	return charIsC0Control(char) or (char >= 0x7F and char <= 0x9F)

def tagIsSpecial(tagName: str, nameSpace: str = "html") -> bool:
	# Namespace support is still missing so fixed to html.
	if (nameSpace == "html"):
		return tagName in [
			"address",
			"applet",
			"area",
			"article",
			"aside",
			"base",
			"basefont",
			"bgsound",
			"blockquote",
			"body",
			"br",
			"button",
			"caption",
			"center",
			"col",
			"colgroup",
			"dd",
			"details",
			"dir",
			"div",
			"dl",
			"dt",
			"embed",
			"fieldset",
			"figcaption",
			"figure",
			"footer",
			"form",
			"frame",
			"frameset",
			"h1",
			"h2",
			"h3",
			"h4",
			"h5",
			"h6",
			"head",
			"header",
			"hgroup",
			"hr",
			"html",
			"iframe",
			"img",
			"input",
			"keygen",
			"li",
			"link",
			"listing",
			"main",
			"marquee",
			"menu",
			"meta",
			"nav",
			"noembed",
			"noframes",
			"noscript",
			"object",
			"ol",
			"p",
			"param",
			"plaintext",
			"pre",
			"script",
			"section",
			"select",
			"source",
			"style",
			"summary",
			"table",
			"tbody",
			"td",
			"template_",
			"textarea",
			"tfoot",
			"th",
			"thead",
			"title",
			"tr",
			"track",
			"ul",
			"wbr",
			"xmp"
		]
	elif (nameSpace == "svg"):
		return tagName in [
			"desc",
			"foreignObject",
			"title"
		]
	elif (nameSpace == "Mathml"):
		raise NotImplemented

	return False
