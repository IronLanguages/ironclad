
import os, sys

from tools.utils.apiplumbing import generate_api_plumbing
from tools.utils.codegen import eval_dict_item
from tools.utils.file import read_interesting_lines, write
from tools.utils.gccxml import generate_api_signatures, generate_api_structs, in_set, prefixed, read_gccxml


def read_all_inputs(src):
    def read_data(name):
        return read_interesting_lines(src, name)

    def read_args_kwargs(name, argcount, context=None):
        result = []
        for line in read_data(name):
            _input = line.split(None, argcount)
            result.append((_input[:argcount], eval_dict_item(_input[argcount:], context)))
        return result

    DISPATCHER_FIELDS = read_args_kwargs('_dispatcher_fields', 3)
    DISPATCHER_METHODS = read_args_kwargs('_dispatcher_methods', 2, 'data.snippets.cs.dispatcher')

    MAGICMETHODS = read_args_kwargs('_magicmethods', 3, 'data.snippets.cs.magicmethods')

    ALL_API_FUNCTIONS = set(read_data('_visible_api_functions.generated'))
    PURE_C_SYMBOLS = set(read_data('_dont_register_symbols'))
    MGD_API_DATA = [{'symbol': s} for s in read_data('_mgd_api_data')]

    global_ = read_gccxml(os.path.join(src, '_api.generated.xml'))

    mgd_api_struct_names = set(read_data('_mgd_api_structs'))
    MGD_API_STRUCTS = set(generate_api_structs(global_.classes(in_set(mgd_api_struct_names))))
    MGD_API_STRUCTS |= set(generate_api_structs(global_.typedefs(in_set(mgd_api_struct_names))))

    mgd_api_function_names = set(read_data('_mgd_api_functions'))
    ALL_MGD_FUNCTIONS = set(generate_api_signatures(global_.free_functions(in_set(mgd_api_function_names))))
    ALL_MGD_FUNCTIONS |= set(generate_api_signatures(global_.free_functions(prefixed('IC_'))))
    ALL_MGD_FUNCTIONS |= set(generate_api_signatures(global_.variables(prefixed('IC_'))))

    return dict((k, v) for (k, v) in locals().items() if k == k.upper())


if __name__ == '__main__':
    src, dst = sys.argv[1:]
    inputs = read_all_inputs(src)
    files = generate_api_plumbing(inputs)
    for (name, code) in files:
        write(dst, name + '.Generated.cs', code, badge=True)



