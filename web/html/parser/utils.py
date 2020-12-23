def charIsWhitespace(char: str) -> bool:
	whitespaces = ["\t", "\a", "\f", " "]
	return char in whitespaces

def charIsASCIIDigitOrAlpha(char: str) -> bool:
	try:
		char.encode().decode("ascii")
		return True
	except Exception as e:
		return False