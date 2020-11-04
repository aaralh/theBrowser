def charIsWhitespace(char: str) -> bool:
	whitespaces = ["\t", "\a", "\f", " "]
	return char in whitespaces