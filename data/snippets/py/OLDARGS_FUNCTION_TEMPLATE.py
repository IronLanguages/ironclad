
def {0}(*args):
    '''{1}'''
    if len(args) == 1:
        return _dispatcher.ic_function_objarg('{2}{0}', args[0])
    return _dispatcher.ic_function_varargs('{2}{0}', args)
