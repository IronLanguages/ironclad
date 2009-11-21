
import os, sys
import operator

from pygccxml import declarations as decl

from tools.utils.funcspec import FuncSpec


#===============================================================================
# moderately cute name-matcher-factory and products
# example usage:
#     ns.free_functions(prefixed('PyString'))
#     ns.free_functions(prefixed('PyString PyList'))
#     ns.free_functions(containing('StringAnd InitModule'))

def _make_querymaker(decider):
    def _get_match(target):
        return lambda obj: decider(obj.name, target)
    
    def querymaker(targets):
        if isinstance(targets, basestring):
            matches = map(_get_match, targets.split())
        else:
            matches = [_get_match(targets)]
        
        def query(target):
            for match in matches:
                if match(target):
                    return True
        
        return query
    
    return querymaker

equal = _make_querymaker(str.__eq__)
prefixed = _make_querymaker(str.startswith)
containing = _make_querymaker(str.__contains__)
in_set = _make_querymaker(lambda name, target: name in target)


#===============================================================================
# convert pygccxml types into ictypes

_DECL_HANDLERS = {
    'Py_complex':           'cpx',
    'PyGILState_STATE':     'int', # has worked well enough so far
    'Py_UNICODE':           'ucchar',
    'PyThread_type_lock':   'ptr', # has worked well enough so far
    'size_t':               'size',
    'Py_ssize_t':           'ssize',
}

def _handle_declarated(dec):
    return _DECL_HANDLERS.get(str(dec), '?%s?' % dec)

def _handle_ptr(ptr):
    base = str(ptr.base)
    if base in ('char', 'char const'):
        return 'str'
    if base == '_typeobject':
        return 'obj'
    if base.startswith('Py') and base.endswith('Object'):
        return 'obj'
    return 'ptr'

def _handle_array(array):
    if array.size != 1:
        raise NotImplementedError('array with more than one element')
    return _get_ictype(array.base)

def _ictype(result):
    return lambda _: result

_TYPE_HANDLERS = {
    decl.pointer_t:                 _handle_ptr,
    decl.declarated_t:              _handle_declarated,
    decl.array_t:                   _handle_array,
    decl.void_t:                    _ictype('void'),
    decl.bool_t:                    _ictype('bool'),
    decl.char_t:                    _ictype('char'),
    decl.wchar_t:                   _ictype('wchar'),
    decl.int_t:                     _ictype('int'),
    decl.unsigned_int_t:            _ictype('uint'),
    decl.long_int_t:                _ictype('long'),
    decl.long_unsigned_int_t:       _ictype('ulong'),
    decl.long_long_int_t:           _ictype('llong'),
    decl.long_long_unsigned_int_t:  _ictype('ullong'),
    decl.double_t:                  _ictype('double'),
    decl.ellipsis_t:                _ictype('...'),
}

def _get_ictype(t):
    default = _ictype('?%s %s?' % (type(t), t))
    handler = _TYPE_HANDLERS.get(type(t), default)
    return handler(t)


#===============================================================================
# decorator for generate_ functions to allow simpler calls

def _combine_calls(f):
    def g(*args):
        getresult = lambda x: set(f(x))
        return reduce(operator.or_, map(getresult, args), set())
    return g


#===============================================================================
# convert pygccxml functions into FuncSpecs

def _func_from_typedef(t):
    if not isinstance(t.type, decl.pointer_t):
        return
    return t.type.base

_FUNC_HANDLERS = {
    decl.free_function_t:   lambda f: f.function_type(),
    decl.variable_t:        lambda v: v.type.declaration.type.base,
    decl.typedef_t:         _func_from_typedef,
}

def _get_funcspec(func):
    func_type = _FUNC_HANDLERS[type(func)](func)
    if not func_type:
        return
    ret = _get_ictype(func_type.return_type)
    args = map(_get_ictype, func_type.arguments_types)
    return func.name, FuncSpec(ret, args)

@_combine_calls
def get_funcspecs(items):
    return filter(None, map(_get_funcspec, items))


#===============================================================================
# convert pygccxml structs into struct specs

_STRUCT_HANDLERS = {
    decl.class_t:           lambda f: f.get_members(),
    decl.typedef_t:         lambda t: t.type.declaration.get_members(),
}

def _get_structspec(struct):
    struct_members = _STRUCT_HANDLERS[type(struct)](struct)
    members = [m for m in struct_members if isinstance(m, decl.variable_t)]
    struct_spec = []
    for member in members:
        struct_spec.append((member.name, _get_ictype(member.type)))
    return struct.name, tuple(struct_spec)

@_combine_calls
def get_structspecs(structs):
    return map(_get_structspec, structs)
    

#==========================================================================



