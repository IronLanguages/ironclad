
import os, sys

from tools.utils.apiplumbing import generate_apiplumbing
from tools.utils.io import eval_kwargs_column, read_interesting_lines, write
from tools.utils.gccxml import generate_api_funcspecs, generate_api_structs, in_set, prefixed, read_gccxml


#==========================================================================

def _unpack_mgd_api_functions(mgd_api_function_inputs):
    unstring_names = set()
    mgd_api_function_names = set()
    def unpack_collect(name, unstring=False):
        mgd_api_function_names.add(name)
        if unstring:
            unstring_names.add(name)
    
    for (args, kwargs) in mgd_api_function_inputs:
        unpack_collect(*args, **kwargs)
    return mgd_api_function_names, unstring_names

def _tweak_mgd_api_functions(mgd_api_functions, unstring_names):
    tweaked = dict(mgd_api_functions)
    for (name, spec) in mgd_api_functions:
        if name in unstring_names:
            tweaked[name] = spec.unstringed
    return tweaked.items()

def read_all_inputs(src):
    def read_data(name):
        return read_interesting_lines(src, name)

    def read_args_kwargs(name, argcount, context=None):
        result = []
        for line in read_data(name):
            _input = line.split(None, argcount)
            result.append((_input[:argcount], eval_kwargs_column(_input[argcount:], context)))
        return result

    DISPATCHER_FIELDS = read_args_kwargs('_dispatcher_fields', 3)
    DISPATCHER_METHODS = read_args_kwargs('_dispatcher_methods', 2, 'data.snippets.cs.dispatcher')

    MAGICMETHODS = read_args_kwargs('_magicmethods', 3, 'data.snippets.cs.magicmethods')

    ALL_API_FUNCTIONS = set(read_data('_visible_api_functions.generated'))
    PURE_C_SYMBOLS = set(read_data('_dont_register_symbols'))
    MGD_API_DATA = [{'symbol': s} for s in read_data('_mgd_api_data')]

    gccxml = read_gccxml(os.path.join(src, '_api.generated.xml'))

    mgd_api_struct_names = set(read_data('_mgd_api_structs'))
    MGD_API_STRUCTS = set(generate_api_structs(gccxml.classes(in_set(mgd_api_struct_names))))
    MGD_API_STRUCTS |= set(generate_api_structs(gccxml.typedefs(in_set(mgd_api_struct_names))))

    mgd_api_functions = read_args_kwargs('_mgd_api_functions', 1)
    mgd_api_function_names, unstring_names = _unpack_mgd_api_functions(mgd_api_functions)
    all_mgd_functions = set(generate_api_funcspecs(gccxml.free_functions(in_set(mgd_api_function_names))))
    all_mgd_functions |= set(generate_api_funcspecs(gccxml.free_functions(prefixed('IC_'))))
    all_mgd_functions |= set(generate_api_funcspecs(gccxml.variables(prefixed('IC_'))))
    ALL_MGD_FUNCTIONS = _tweak_mgd_api_functions(all_mgd_functions, unstring_names)

    return dict((k, v) for (k, v) in locals().items() if k == k.upper())


#==========================================================================

if __name__ == '__main__':
    src, dst = sys.argv[1:]
    inputs = read_all_inputs(src)
    files = generate_apiplumbing(inputs)
    
    for (name, code) in files:
        write(dst, name + '.Generated.cs', code, badge=True)



