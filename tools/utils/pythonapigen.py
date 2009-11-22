
from data.snippets.cs.pythonapi import *


from tools.utils.codegen import CodeGenerator, glom_templates, return_dict
from tools.utils.gccxml import get_funcspecs, in_set, prefixed


#==========================================================================

def _symbol_dicts(it):
    return [{'symbol': s} for s in sorted(it)]


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

def _unstring_mgd_api_functions(mgd_api_functions, unstring_names):
    tweaked = dict(mgd_api_functions)
    for (name, spec) in mgd_api_functions:
        if name in unstring_names:
            tweaked[name] = spec.unstringed
    return tweaked.items()


#==========================================================================

class PythonApiGenerator(CodeGenerator):
    # populates self.context.dgt_specs
    
    INPUTS = 'MGD_API_FUNCTIONS EXPORTED_FUNCTIONS PURE_C_SYMBOLS MGD_API_DATA STUBMAIN'
    
    @return_dict('PYTHONAPI')
    def _run(self):
        mgd_api_function_names, unstring_names = _unpack_mgd_api_functions(self.MGD_API_FUNCTIONS)
        all_mgd_functions = get_funcspecs(
            self.STUBMAIN.free_functions(in_set(mgd_api_function_names)),
            self.STUBMAIN.free_functions(prefixed('IC_')),
            self.STUBMAIN.variables(prefixed('IC_')))
        all_mgd_functions = _unstring_mgd_api_functions(all_mgd_functions, unstring_names)
    
        method_infos = []
        not_implemented = self.EXPORTED_FUNCTIONS - self.PURE_C_SYMBOLS
        for (name, spec) in sorted(all_mgd_functions):
            if name in not_implemented:
                not_implemented.remove(name)
            method_infos.append(self._generate_method_info(name, spec))
        not_implemented_method_infos = _symbol_dicts(not_implemented)
        
        api_methods_code = glom_templates('\n\n',
            (METHOD_TEMPLATE, method_infos), 
            (METHOD_NOT_IMPL_TEMPLATE, not_implemented_method_infos),
        )
        getaddress_cases_code = glom_templates('\n',
            (GETADDRESS_CASE_TEMPLATE, method_infos),
            (GETADDRESS_CASE_NOT_IMPL_TEMPLATE, not_implemented_method_infos),
        )

        mgd_data_infos = _symbol_dicts(self.MGD_API_DATA)
        data_properties_code = glom_templates("\n\n",
            (DATA_PROPERTY_TEMPLATE, mgd_data_infos))
        setdata_cases_code = glom_templates("\n",
            (SETDATA_CASE_TEMPLATE, mgd_data_infos))

        return PYTHONAPI_FILE_TEMPLATE % {
            'api_methods': api_methods_code, 
            'getaddress_cases': getaddress_cases_code, 
            'data_properties': data_properties_code, 
            'setdata_cases': setdata_cases_code
        }

    def _generate_method_info(self, name, spec):
        native = spec.native
        self.context.dgt_specs.add(native)
        return {
            "symbol": name,
            "dgt_type": native,
            "return_type": native.mgd_ret,
            "arglist": native.mgd_arglist
        }
    

#==========================================================================
