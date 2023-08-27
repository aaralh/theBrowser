import sys

class JavaScript():

    def __init__(self):
        print("this is the JS engine")



if __name__ == "__main__":
    args = sys.argv
    if len(args) > 1:
        sys.exit(64)
    elif len(args) == 1:
        runFile(args[0])
    else:
        runPrompt()
