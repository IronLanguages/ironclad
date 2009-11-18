
from data.snippets.cs.pythonapi import *

from tools.utils.apiplumbing import ApiPlumbingGenerator
from tools.utils.codegen import generate_arglist, glom_templates, unpack_spec
from tools.utils.type_codes import NATIVETYPES, NATIVETYPE_2_MGDTYPE


class PythonApiGenerator(ApiPlumbingGenerator):
    # populates self.context.dgt_specs
    
    RUN_INPUTS = 'ALL_MGD_FUNCTIONS ALL_API_FUNCTIONS PURE_C_SYMBOLS MGD_API_DATA'
    def _run(self, all_mgd_functions, all_api_functions, pure_c_symbols, mgd_data):
        not_implemented_functions = all_api_functions - pure_c_symbols
        
        methods = []
        for (name, c_spec) in all_mgd_functions:
            if name in not_implemented_functions:
                not_implemented_functions.remove(name)
            methods.append(self._unpack_apifunc(name, c_spec))
            
        not_implemented_methods = [{"symbol": s} for s in not_implemented_functions]
        methods_code = glom_templates('\n\n',
            (PYTHONAPI_METHOD_TEMPLATE, methods), 
            (PYTHONAPI_NOT_IMPLEMENTED_METHOD_TEMPLATE, not_implemented_methods),
        )
        methods_switch = glom_templates('\n',
            (PYTHONAPI_METHOD_CASE, methods),
            (PYTHONAPI_NOT_IMPLEMENTED_METHOD_CASE, not_implemented_methods),
        )

        data_items_code = glom_templates("\n\n",
            (PYTHONAPI_DATA_ITEM_TEMPLATE, mgd_data))
        data_items_switch = glom_templates("\n",
            (PYTHONAPI_DATA_ITEM_CASE, mgd_data))

        return PYTHONAPI_FILE_TEMPLATE % (
            methods_code, methods_switch,
            data_items_code, data_items_switch)
        
        
    def _unpack_apifunc(self, name, ic_spec):
        native_spec, ic_ret, ic_args = self._unpack_ic_spec(ic_spec)
        native_ret, native_args = unpack_spec(native_spec, NATIVETYPES)
        return {
            "symbol": name,
            "dgt_type": native_spec,
            "return_type": NATIVETYPE_2_MGDTYPE[native_ret],
            "arglist": generate_arglist(native_args, NATIVETYPE_2_MGDTYPE)
        }