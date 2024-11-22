import interpreter

def queuebuster(self, **words):
    print("Stopping Lookahead")
    yield interpreter.INTERP_EXECUTE_FINISH