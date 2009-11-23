
#==========================================================================

class CodeGenerator(object):

    INPUTS = ''

    def __init__(self, context=None):
        self.context = context

    def run(self, inputs):
        for attr in self.INPUTS.split():
            setattr(self, attr, inputs[attr])
        return self._run()


#==========================================================================

def glom_templates(joiner, *args):
    output = []
    for (template, inputs) in args:
        for input in inputs:
            output.append(template % input)
    return joiner.join(output)


#==========================================================================

def _dictify(keys, result):
    if len(keys) == 1:
        return { keys[0]: result }
    return dict(zip(keys, result))

def return_dict(keys):
    keys = keys.split()
    def decorator(f):
        def g(*_, **__):
            return _dictify(keys, f(*_, **__))
        return g
    return decorator


#==========================================================================

def starstarmap(func, items):
    for (args, kwargs) in items:
        yield func(*args, **kwargs)


#==========================================================================

def scrunch_filename(name):
    return name[1:].split('.')[0].upper()


#==========================================================================
