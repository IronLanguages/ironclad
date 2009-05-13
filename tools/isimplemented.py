import sys
import os
args = sys.argv[1:]

csharp_funcs = [
    os.path.splitext(name)[0]
    for name in os.listdir("src/python25api_components")]

c_funcs = map(str.strip, file(
    os.path.join('stub', '_ignore_symbols')).readlines())


def check_implemented(name):
    return name in csharp_funcs or name in c_funcs

success = False

for arg in args:
    if not check_implemented(arg):
        success = False
        print arg, "is not implemented"
if not success:
    sys.exit(1)
