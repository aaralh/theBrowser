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
