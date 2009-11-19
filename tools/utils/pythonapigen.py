
from data.snippets.cs.pythonapi import *

from tools.utils.apiplumbing import ApiPlumbingGenerator


#==========================================================================

def _glom_templates(joiner, *args):
    output = []
    for (template, inputs) in args:
        for input in inputs:
            output.append(template % input)
    return joiner.join(output)


#==========================================================================

class PythonApiGenerator(ApiPlumbingGenerator):
    # populates self.context.dgt_specs
    
    RUN_INPUTS = 'ALL_MGD_FUNCTIONS ALL_API_FUNCTIONS PURE_C_SYMBOLS MGD_API_DATA'
    
    def _run(self, all_mgd_functions, all_api_functions, pure_c_symbols, mgd_data):
        method_infos = []
        not_implemented = all_api_functions - pure_c_symbols
        for (name, spec) in all_mgd_functions:
            if name in not_implemented:
                not_implemented.remove(name)
            method_infos.append(self._generate_method_info(name, spec))
        not_implemented_methods = [{"symbol": s} for s in not_implemented]
        
        methods_code = _glom_templates('\n\n',
            (METHOD_TEMPLATE, method_infos), 
            (METHOD_NOT_IMPL_TEMPLATE, not_implemented_methods),
        )
        
        methods_switch_code = _glom_templates('\n',
            (GETADDRESS_CASE_TEMPLATE, method_infos),
            (GETADDRESS_CASE_NOT_IMPL_TEMPLATE, not_implemented_methods),
        )

        data_code = _glom_templates("\n\n",
            (DATA_PROPERTY_TEMPLATE, mgd_data))
        
        data_switch_code = _glom_templates("\n",
            (SETDATA_CASE_TEMPLATE, mgd_data))

        return PYTHONAPI_FILE_TEMPLATE % (
            methods_code, methods_switch_code, data_code, data_switch_code)
        
        
    def _generate_method_info(self, name, spec):
        native = spec.native
        self.context.dgt_specs.add(native)
        return {
            "symbol": name,
            "dgt_type": native,
            "return_type": native.mgd_ret,
            "arglist": native.mgd_arglist
        }



