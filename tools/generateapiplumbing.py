
import os, sys

from tools.utils.apiplumbing import generate_apiplumbing
from tools.utils.io import eval_kwargs_column, read_interesting_lines, write
from tools.utils.gccxml import read_gccxml


#==========================================================================

def read_all_inputs(src):
    GCCXML = read_gccxml(os.path.join(src, '_api.generated.xml'))
    
    def read_data(name):
        return set(read_interesting_lines(src, name))

    MGD_API_DATA = read_data('_mgd_api_data')
    MGD_API_STRUCTS = read_data('_mgd_api_structs')
    PURE_C_SYMBOLS = read_data('_pure_c_symbols')
    EXPORTED_FUNCTIONS = read_data('_exported_functions.generated')

    def read_args_kwargs(name, argcount, context=None):
        result = []
        for line in read_data(name):
            _input = line.split(None, argcount)
            result.append((_input[:argcount], eval_kwargs_column(_input[argcount:], context)))
        return result

    MGD_API_FUNCTIONS = read_args_kwargs('_mgd_api_functions', 1)
    DISPATCHER_FIELDS = read_args_kwargs('_dispatcher_fields', 3)
    DISPATCHER_METHODS = read_args_kwargs('_dispatcher_methods', 1, 'data.snippets.cs.dispatcher')
    MAGICMETHODS = read_args_kwargs('_magicmethods', 3, 'data.snippets.cs.magicmethods')

    return dict((k, v) for (k, v) in locals().items() if k == k.upper())


#==========================================================================

if __name__ == '__main__':
    src, dst = sys.argv[1:]
    inputs = read_all_inputs(src)
    files = generate_apiplumbing(inputs)
    
    for (name, code) in files:
        write(dst, name + '.Generated.cs', code, badge=True)



