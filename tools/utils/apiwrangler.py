
from tools.utils import dispatchergen as DGen
from tools.utils import magicmethodgen as MMGen

from tools.utils.codegen import generate_arglist, glom_templates, multi_update, pack_spec, unpack_spec, starstarmap
from tools.utils.file import read_interesting_lines
from tools.utils.structgen import generate_struct
from tools.utils.type_codes import CTYPES, CTYPE_2_DGTTYPE, DGTTYPES, DGTTYPE_2_MGDTYPE

from data.snippets.cs.dgttype import *
from data.snippets.cs.dispatcher import *
from data.snippets.cs.magicmethods import *
from data.snippets.cs.pythonapi import *
from data.snippets.cs.structs import *

class ApiWrangler(object):

    def __init__(self, input):
        self.dispatcher_methods = {}
        self.dgt_specs = set()
        self.output = {}
        
        # Order of the following operations is important!
        
        self.output['structs_code'] = self.generate_structs(
            input['MGD_API_STRUCTS'])
        
        self.output['dispatcher_code'] = self.generate_dispatcher(
            input['DISPATCHER_FIELDS'], 
            input['DISPATCHER_METHODS'])
            
        self.output['magicmethods_code'] = self.generate_magic_methods(
            input['MAGICMETHODS'])
            
        self.output['pythonapi_code'] = self.generate_pythonapi(
            input['MGD_API_FUNCTIONS'], 
            input['MGD_NONAPI_FUNCTIONS'], 
            input['ALL_API_FUNCTIONS'], 
            input['PURE_C_SYMBOLS'], 
            input['MGD_API_DATA'])
            
        self.output['dgttype_code'] = self.generate_dgts()


    def _unpack_c_spec(self, c_spec):
        ret, args = unpack_spec(c_spec, CTYPES)
        dgt_spec = pack_spec(ret, args, CTYPE_2_DGTTYPE)
        self.dgt_specs.add(dgt_spec)
        return dgt_spec, ret, args 
        
        
    def _unpack_apifunc(self, name, c_spec):
        dgt_spec, ret, args = self._unpack_c_spec(c_spec)
        dgt_ret, dgt_args = unpack_spec(dgt_spec, DGTTYPES)
        return {
            "symbol": name,
            "dgt_type": dgt_spec,
            "return_type": DGTTYPE_2_MGDTYPE[dgt_ret],
            "arglist": generate_arglist(dgt_args, DGTTYPE_2_MGDTYPE)
        }


    def _generate_dgttype(self, dgt_spec):
        ret, args = unpack_spec(dgt_spec, DGTTYPES)
        return DGTTYPE_TEMPLATE % {
            'name': dgt_spec,
            'rettype': DGTTYPE_2_MGDTYPE[ret], 
            'arglist': generate_arglist(args, DGTTYPE_2_MGDTYPE)
        }


    def _generate_dispatcher_method(self, name, c_spec, argtweak=None, rettweak='', nullablekwargs=None):
        dgt_spec, c_ret, c_args = self._unpack_c_spec(c_spec)
        mgd_arg_types, dgt_arg_names = DGen.expand_args(c_args, argtweak)
        
        self.dispatcher_methods[name] = (mgd_arg_types, dgt_spec)
        info = {
            'signature': DGen.method_signature(name, c_ret, mgd_arg_types),
            'call': DGen.method_dgt_call(dgt_spec, dgt_arg_names),
        }
        multi_update(info, 
            ('translate_objs', 'cleanup_objs'), DGen.method_obj_translation(mgd_arg_types, nullablekwargs))
        multi_update(info, 
            ('store_ret', 'handle_ret', 'return_ret'), DGen.method_ret_handling(c_ret, rettweak))
        return METHOD_TEMPLATE % info


    def generate_structs(self, struct_specs):
        return STRUCTS_FILE_TEMPLATE % '\n\n'.join(map(generate_struct, struct_specs))


    def generate_dispatcher(self, field_types, method_types):
        dispatcher_fields = '\n\n'.join(starstarmap(DGen.field, field_types))
        dispatcher_methods = '\n\n'.join(starstarmap(self._generate_dispatcher_method, method_types))
        return DISPATCHER_FILE_TEMPLATE % '\n\n'.join((dispatcher_fields, dispatcher_methods))


    def generate_magic_methods(self, protocol_field_types):
        # this depends on self.dispatcher_methods having been populated (by dispatcher generation)
        normal_magic_methods = []
        swapped_magic_methods = []
        def generate_magic_method(cslotname, functype, pyslotname, swappedname=None, template=MAGICMETHOD_TEMPLATE_TEMPLATE, swappedtemplate=MAGICMETHOD_TEMPLATE_TEMPLATE):
            inargs, dgttype = self.dispatcher_methods[functype]
            needswap = MAGICMETHOD_NEEDSWAP_NO
            if swappedname is not None:
                swappedtemplate = MMGen.swapped_template(functype, inargs, swappedtemplate)
                swapped_magic_methods.append(MAGICMETHOD_CASE % (cslotname, swappedname, MAGICMETHOD_NEEDSWAP_NO, dgttype, swappedtemplate))
                needswap = MAGICMETHOD_NEEDSWAP_YES
            template = MMGen.template(functype, inargs, template)
            normal_magic_methods.append(MAGICMETHOD_CASE % (cslotname, pyslotname, needswap, dgttype, template))
        
        for (args, kwargs) in protocol_field_types:
            generate_magic_method(*args, **kwargs)
        
        return MAGICMETHODS_FILE_TEMPLATE % ('\n\n'.join(normal_magic_methods), '\n\n'.join(swapped_magic_methods))


    def generate_pythonapi(self, mgd_pythonapi_functions, mgd_nonapi_c_functions, all_api_functions, pure_c_symbols, mgd_data):
        all_mgd_functions = mgd_pythonapi_functions | mgd_nonapi_c_functions
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

        data_items_code = glom_templates("\n\n", (PYTHONAPI_DATA_ITEM_TEMPLATE, mgd_data))
        data_items_switch = glom_templates("\n", (PYTHONAPI_DATA_ITEM_CASE, mgd_data))

        return PYTHONAPI_FILE_TEMPLATE % (
            methods_code, methods_switch,
            data_items_code, data_items_switch)
            

    def generate_dgts(self):
        # this depends on self.dgt_specs having been populated (by dispatcher and pythonapi construction)
        return FILE_TEMPLATE % '\n'.join(map(self._generate_dgttype, sorted(self.dgt_specs)))


