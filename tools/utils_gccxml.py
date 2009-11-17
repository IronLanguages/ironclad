
import sys
import operator

import pygccxml
from pygccxml import declarations as decl
from pygccxml.parser.config import config_t
from pygccxml.parser.source_reader import source_reader_t

#===============================================================================
# ugly patch

if sys.platform == 'cli':
    # we're not trying to invoke gccxml anyway, so this shouldn't matter
    pygccxml.parser.config.gccxml_configuration_t.raise_on_wrong_settings = lambda _: None

#===============================================================================
# convert pygccxml types into intermediate representation
# suitable for later conversion as defined in platform.py

_DECL_HANDLERS = {
    'Py_complex':           'cpx',
    'PyGILState_STATE':     'int', # has worked well enough so far
    'Py_UNICODE':           'uchar',
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
    if base.startswith('Py') and base.endswith('Object'):
        return 'obj'
    return 'ptr'

def _ret(result):
    return lambda _: result

_TYPE_HANDLERS = {
    decl.pointer_t:                 _handle_ptr,
    decl.declarated_t:              _handle_declarated,
    decl.void_t:                    _ret('void'),
    decl.bool_t:                    _ret('bool'),
    decl.char_t:                    _ret('char'),
    decl.wchar_t:                   _ret('wchar'),
    decl.int_t:                     _ret('int'),
    decl.unsigned_int_t:            _ret('uint'),
    decl.long_int_t:                _ret('long'),
    decl.long_unsigned_int_t:       _ret('ulong'),
    decl.long_long_int_t:           _ret('llong'),
    decl.long_long_unsigned_int_t:  _ret('ullong'),
    decl.double_t:                  _ret('double'),
    decl.ellipsis_t:                _ret('...'),
}

def get_type_name(t):
    default = _ret('?%s %s?' % (type(t), t))
    handler = _TYPE_HANDLERS.get(type(t), default)
    return handler(t)

_FUNC_HANDLERS = {
    decl.free_function_t:   lambda f: f.function_type(),
    decl.variable_t:        lambda v: v.type.declaration.type.base,
}

def _get_func_info(func):
    func_type = _FUNC_HANDLERS[type(func)](func)
    ret_type = get_type_name(func_type.return_type)
    arg_types = ''.join(map(get_type_name, func_type.arguments_types)) or 'void'
    return func.name, '_'.join((ret_type, arg_types))

def extract_signatures(functions):
    return map(_get_func_info, functions)

#===============================================================================
# moderately cute name-matcher-factory

def makequerymaker(decider):
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

prefixed = makequerymaker(str.startswith)
containing = makequerymaker(str.__contains__)
in_set = makequerymaker(lambda name, target: name in target)

# example usage:
#     ns.free_functions(prefixed('PyString'))
#     ns.free_functions(prefixed('PyString PyList'))
#     ns.free_functions(containing('StringAnd InitModule'))


#===============================================================================
# read generated xml

def read_gccxml(path):
    return source_reader_t(config_t()).read_xml_file(path)[0]


#===============================================================================
# 

def generate_api_signatures(source, query):
    functions = source(query)
    signatures = dict(extract_signatures(functions))
    for name in signatures:
        if 'PyString' in name:
            # we don't want these particular char* arguments to be marshalled automatically
            signatures[name] = signatures[name].replace('str', 'ptr')
    return signatures.items()

