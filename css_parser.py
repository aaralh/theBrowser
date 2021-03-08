import tinycss2


#parser = tinycss2.make_parser('page3')

with open("simple.css", "r") as cssFile:
    css = cssFile.read()

rules = tinycss2.parse_stylesheet(css)

print(rules)

for rule in rules:
    print(rule)
