
from os import listdir
from os.path import isfile, join
onlyfiles = [f for f in listdir(".") if isfile(join(".", f))]

with open('somefile.py', 'a') as the_file:
	for fileName in onlyfiles:
		name = fileName.split(".")[0]
		the_file.write(f"import web.dom.elements.{name} as {name}\n")