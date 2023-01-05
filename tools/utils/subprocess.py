import os

def popen(executable, arguments):
    return os.popen(executable + " " + arguments)
