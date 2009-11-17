
#===============================================

def generate_arglist(arg_types, type_dict):
    return ', '.join('%s arg%d' % (type_dict[arg], i) for (i, arg) in enumerate(arg_types))

#===============================================

def _slurp_argstr(set_, argstr):
    while len(argstr):
        for key in set_:
            if argstr.startswith(key):
                argstr = argstr[len(key):]
                yield key
                break
        else:
            raise Exception('could not understand arg type: "%s"' % argstr)

def _unpack_argstr(set_, argstr):
    if argstr == 'void':
        return ()
    return tuple(_slurp_argstr(set_, argstr))

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




