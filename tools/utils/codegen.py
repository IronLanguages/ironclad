

#==========================================================================

class CodeGenerator(object):

    INPUTS = ''

    def run(self, inputs):
        for attr in self.INPUTS.split():
            setattr(self, attr, inputs[attr])
        return self._run()


#==========================================================================

def eval_kwargs_column(container, context=None):
    if not container:
        return {}
    str_, ctx = container[0], {}
    if context is not None:
        ctx = __import__(context, fromlist=['*']).__dict__
    return eval(str_, ctx)


#==========================================================================

def filter_keys_uppercase(d):
    return dict((k, v) for (k, v) in d.items() if k == k.upper())


#==========================================================================

def glom_templates(joiner, *args):
    output = []
    for (template, inputs) in args:
        for input in inputs:
            output.append(template % input)
    return joiner.join(output)


#==========================================================================

def return_dict(keys):
    def decorator(f):
        def g(*_, **__):
            return dict(zip(keys.split(), f(*_, **__)))
        return g
    return decorator


#==========================================================================
