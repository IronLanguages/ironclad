
from tools.utils.ictypes import canonical_ictype, native_ictype, unstringed_ictype, VALID_ICTYPES
from tools.utils.platform import ICTYPE_2_MGDTYPE


#==========================================================================

class _FuncSpec(tuple):
    
    @property
    def ret(self):
        return self[0]
    
    @property
    def args(self):
        return self[1:]

    @property
    def argspec(self):
        return ''.join(self.args) or 'void'
    
    @property
    def mgd_ret(self):
        return ICTYPE_2_MGDTYPE[self.ret]

    @property
    def mgd_arglist(self):
        return ', '.join(
            '%s arg%d' % (ICTYPE_2_MGDTYPE[arg], i)
            for (i, arg) in enumerate(self.args))

    @property
    def canonical(self):
        return _FuncSpec(map(canonical_ictype, self))

    @property
    def native(self):
        return _FuncSpec(map(native_ictype, self))

    @property
    def unstringed(self):
        return _FuncSpec(map(unstringed_ictype, self))

    def withargs(self, newargs):
        return _FuncSpec(self[:1] + tuple(newargs))

    def __str__(self):
        return '_'.join((self.ret, self.argspec))

    def __repr__(self):
        return 'FuncSpec("%s")' % self


#==========================================================================

def _complain(s):
    raise Exception('could not get ictype from "%s"' % s)

def _slurp_argspec(argspec):
    while len(argspec):
        for key in VALID_ICTYPES:
            if argspec.startswith(key):
                argspec = argspec[len(key):]
                yield key
                break
        else:
            _complain(argspec)

def _unpack_argspec(argspec):
    if argspec == 'void':
        return ()
    return tuple(_slurp_argspec(argspec))

def _unpack_retargs(ret, args):
    return (ret,) + tuple(args)

def _unpack_funcspec(funcspec):
    ret, argspec = funcspec.split('_')
    if ret not in VALID_ICTYPES:
        _complain(ret)
    args = _unpack_argspec(argspec)
    return _unpack_retargs(ret, args)

_unpack_nothing = lambda x: x

_UNPACKERS = {
    (str,):         _unpack_funcspec,
    (str, list):    _unpack_retargs,
    (str, tuple):   _unpack_retargs,
}

def _get_funcspec_data(input):
    types = tuple(map(type, input))
    unpack = _UNPACKERS.get(types, _unpack_nothing)
    return unpack(*input)


#==========================================================================

def FuncSpec(*args):
    return _FuncSpec(_get_funcspec_data(args)).canonical
    

#==========================================================================
