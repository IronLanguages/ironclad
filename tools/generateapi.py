
import sys
src, dst = sys.argv[1:]

from tools.apiwrangler import ApiWrangler
from tools.utils import eval_dict_item, read_interesting_lines, write
from tools.utils_gccxml import generate_api_signatures, in_set, prefixed, read_gccxml

#==============================================================================

def read_data(name):
    return read_interesting_lines(src, name)

def read_args_kwargs(name, argcount, context=None):
    result = []
    for line in read_data(name):
        _input = line.split(None, argcount)
        result.append((_input[:argcount], eval_dict_item(_input[argcount:], context)))
    return result

def write_output(key, name):
    dstname = name + '.Generated.cs'
    write(dst, dstname, wrangler.output[key], badge=True)

#==============================================================================


DISPATCHER_FIELDS = read_args_kwargs('_dispatcher_fields', 3)
DISPATCHER_METHODS = read_args_kwargs('_dispatcher_methods', 2, 'data.snippets.cs.dispatcher')
MAGICMETHODS = read_args_kwargs('_magicmethods', 3, 'data.snippets.cs.magicmethods')
ALL_API_FUNCTIONS = set(read_data("_visible_api_functions.generated"))
PURE_C_SYMBOLS = set(read_data("_dont_register_symbols"))
MGD_API_DATA = [{'symbol': s} for s in read_data("_mgd_api_data") if s not in PURE_C_SYMBOLS]

global_ = read_gccxml('data/api/_api.generated.xml')
MGD_NONAPI_FUNCTIONS = set(generate_api_signatures(global_.free_functions, prefixed('IC_')))
MGD_NONAPI_FUNCTIONS |= set(generate_api_signatures(global_.variables, prefixed('IC_')))

mgd_api_function_names = set(read_data("_mgd_api_functions"))
MGD_API_FUNCTIONS = set(generate_api_signatures(global_.free_functions, in_set(mgd_api_function_names)))

wrangler = ApiWrangler(locals())

write_output('magicmethods_code', 'MagicMethods')
write_output('pythonapi_code', 'PythonApi')
write_output('dispatcher_code', 'Dispatcher')
write_output('dgttype_code', 'Delegates')


