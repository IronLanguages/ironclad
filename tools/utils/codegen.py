
#===============================================

def generate_arglist(arg_types, type_dict):
    return ', '.join('%s arg%d' % (type_dict[arg], i) for (i, arg) in enumerate(arg_types))

#===============================================

def _slurp_argstr(types, argstr):
    while len(argstr):
        for key in types:
            if argstr.startswith(key):
                argstr = argstr[len(key):]
                yield key
                break
        else:
            raise Exception('could not understand arg type: "%s"' % argstr)

def _unpack_argstr(types, argstr):
    if argstr == 'void':
        return ()
    return tuple(_slurp_argstr(types, argstr))

def unpack_spec(spec, types):
    ret, argstr = spec.split('_')
    if ret not in types:
        raise Exception('could not understand ret type: "%s"' % ret)
    args = _unpack_argstr(types, argstr)
    return ret, args

#===============================================

def pack_spec(ret, args, dict_):
    tweak = lambda x: dict_.__getitem__(x)
    return '_'.join((tweak(ret), ''.join(map(tweak, args)) or 'void'))

#====================================================================

def eval_dict_item(container, context=None):
    if not container:
        return {}
    str_, ctx = container[0], {}
    if context is not None:
        ctx = __import__(context, fromlist=['*']).__dict__
    return eval(str_, ctx)

#====================================================================

def starstarmap(func, items):
    for (args, kwargs) in items:
        yield func(*args, **kwargs)

def glom_templates(joiner, *args):
    output = []
    for (template, inputs) in args:
        for input in inputs:
            output.append(template % input)
    return joiner.join(output)

def multi_update(dict_, names, values):
    for (name, value) in zip(names, values):
        dict_[name] = value

#====================================================================


