
import sys
src, dst = sys.argv[1:]

from tools.apiwrangler import ApiWrangler
from tools.c_utils import name_spec_from_c
from tools.utils import eval_dict_item, read_interesting_lines, write

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
MGD_API_FUNCTIONS = set(map(lambda x: tuple(x.split()), read_data("_mgd_api_functions")))
MGD_NONAPI_C_FUNCTIONS = set(map(name_spec_from_c, read_data("_mgd_function_prototypes")))
ALL_API_FUNCTIONS = set(read_data("_visible_api_functions.generated"))
PURE_C_SYMBOLS = set(read_data("_dont_register_symbols"))
MGD_API_DATA = [{'symbol': s} for s in read_data("_mgd_api_data") if s not in PURE_C_SYMBOLS]
EXTRA_DGTTYPES = set(read_data("_extra_dgttypes"))

wrangler = ApiWrangler(locals())

write_output('magicmethods_code', 'MagicMethods')
write_output('pythonapi_code', 'PythonApi')
write_output('dispatcher_code', 'Dispatcher')
write_output('dgttype_code', 'Delegates')


