
from tools.utils import dispatchergen
from tools.utils import magicmethodsgen

from tools.utils.codegen import generate_arglist, glom_templates, multi_update, pack_spec, unpack_spec, starstarmap
from tools.utils.dgttypegen import generate_dgttype
from tools.utils.file import read_interesting_lines
from tools.utils.structsgen import generate_struct
from tools.utils.type_codes import ICTYPES, ICTYPE_2_NATIVETYPE, NATIVETYPES, NATIVETYPE_2_MGDTYPE

from data.snippets.cs.dgttype import *
from data.snippets.cs.dispatcher import *
from data.snippets.cs.magicmethods import *
from data.snippets.cs.pythonapi import *
from data.snippets.cs.structs import *


class ApiWrangler(object):

    def __init__(self, input):
        self._dgt_specs = set()
        self._dispatcher_methods = {}
        self._normal_magicmethods = []
        self._swapped_magicmethods = []
        
        self.output = {}
        # Order of the following operations is important!
        
        self.output['structs_code'] = self.generate_structs(
            input['MGD_API_STRUCTS'])
        
        self.output['dispatcher_code'] = self.generate_dispatcher(
            input['DISPATCHER_FIELDS'], 
            input['DISPATCHER_METHODS'])
            
        self.output['magicmethods_code'] = self.generate_magicmethods(
            input['MAGICMETHODS'])
            
        self.output['pythonapi_code'] = self.generate_pythonapi(
            input['ALL_MGD_FUNCTIONS'], 
            input['ALL_API_FUNCTIONS'], 
            input['PURE_C_SYMBOLS'], 
            input['MGD_API_DATA'])
            
        self.output['dgttype_code'] = self.generate_dgttypes()


    def _unpack_ic_spec(self, ic_spec):
        ic_ret, ic_args = unpack_spec(ic_spec, ICTYPES)
        native_spec = pack_spec(ic_ret, ic_args, ICTYPE_2_NATIVETYPE)
        self._dgt_specs.add(native_spec)
        return native_spec, ic_ret, ic_args
        
        
    def _unpack_apifunc(self, name, ic_spec):
        native_spec, ic_ret, ic_args = self._unpack_ic_spec(ic_spec)
        native_ret, native_args = unpack_spec(native_spec, NATIVETYPES)
        return {
            "symbol": name,
            "dgt_type": native_spec,
            "return_type": NATIVETYPE_2_MGDTYPE[native_ret],
            "arglist": generate_arglist(native_args, NATIVETYPE_2_MGDTYPE)
        }


    def _generate_dispatcher_method(self, name, ic_spec, arg_tweak=None, ret_tweak='', nullable_kwargs=None):
        native_spec, ic_ret, ic_args = self._unpack_ic_spec(ic_spec)
        mgd_args, native_arg_names = dispatchergen.expand_args(ic_args, arg_tweak)
        
        self._dispatcher_methods[name] = (mgd_args, native_spec)
        info = {
            'signature': dispatchergen.method_signature(name, ic_ret, mgd_args),
            'call': dispatchergen.method_dgt_call(native_spec, native_arg_names),
        }
        multi_update(info, 
            ('translate_objs', 'cleanup_objs'), 
            dispatchergen.method_obj_translation(mgd_args, nullable_kwargs))
        multi_update(info, 
            ('store_ret', 'handle_ret', 'return_ret'), 
            dispatchergen.method_ret_handling(ic_ret, ret_tweak))
        return METHOD_TEMPLATE % info

        
    def _generate_magicmethod(self, c_field_name, dispatcher_method_name, py_field_name, 
            py_swapped_field_name=None,
            template2=MAGICMETHOD_TEMPLATE_TEMPLATE,
            swapped_template2=MAGICMETHOD_TEMPLATE_TEMPLATE):
        
        # self._dispatcher_methods should have been populated by dispatcher generation
        mgd_args, native_spec = self._dispatcher_methods[dispatcher_method_name]
        needswap = MAGICMETHOD_NEEDSWAP_NO
        
        if py_swapped_field_name is not None:
            needswap = MAGICMETHOD_NEEDSWAP_YES
            swapped_template = magicmethodsgen.swapped_template(dispatcher_method_name, mgd_args, swapped_template2)
            self._swapped_magicmethods.append(MAGICMETHOD_CASE % (
                c_field_name, py_swapped_field_name, MAGICMETHOD_NEEDSWAP_NO, native_spec, swapped_template))
        
        template = magicmethodsgen.normal_template(dispatcher_method_name, mgd_args, template2)
        self._normal_magicmethods.append(MAGICMETHOD_CASE % (
            c_field_name, py_field_name, needswap, native_spec, template))


    def generate_structs(self, struct_specs):
        return STRUCTS_FILE_TEMPLATE % '\n\n'.join(
            map(generate_struct, sorted(struct_specs)))


    def generate_dispatcher(self, field_types, method_types):
        dispatcher_fields = '\n\n'.join(
            starstarmap(dispatchergen.field, field_types))
        dispatcher_methods = '\n\n'.join(
            starstarmap(self._generate_dispatcher_method, method_types))
        return DISPATCHER_FILE_TEMPLATE % '\n\n'.join(
            (dispatcher_fields, dispatcher_methods))


    def generate_magicmethods(self, magicmethods_info):
        for (args, kwargs) in magicmethods_info:
            self._generate_magicmethod(*args, **kwargs)
        
        return MAGICMETHODS_FILE_TEMPLATE % (
            '\n\n'.join(self._normal_magicmethods), 
            '\n\n'.join(self._swapped_magicmethods))


    def generate_pythonapi(self, all_mgd_functions, all_api_functions, pure_c_symbols, mgd_data):
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
            

    def generate_dgttypes(self):
        # self._dgt_specs should have been populated by dispatcher and pythonapi construction
        return FILE_TEMPLATE % '\n'.join(
            map(generate_dgttype, sorted(self._dgt_specs)))


