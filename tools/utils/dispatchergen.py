
from data.snippets.cs.dispatcher import *

from tools.utils.apiplumbing import ApiPlumbingGenerator
from tools.utils.codegen import generate_arglist, multi_update, starstarmap
from tools.utils.type_codes import ICTYPE_2_MGDTYPE

#==========================================================================

def _get_native_argname((index, code)):
    return {'obj': 'ptr%d'}.get(code, 'arg%d') % index

SPECIAL_DISPATCHER_ARG_NAMES = {
    'null': NULL_ARG,
    'module': MODULE_ARG,
}

def _is_normal_arg(arg):
    return arg not in SPECIAL_DISPATCHER_ARG_NAMES

def _expand_args(ic_args, arg_tweak=None):
    if arg_tweak:
        named_args = SPECIAL_DISPATCHER_ARG_NAMES
        mgd_args = [None] * len(filter(_is_normal_arg, arg_tweak))
        native_arg_names = [None] * len(arg_tweak)
        
        for native_arg_pos, native_arg in enumerate(arg_tweak):
            # NOTE: native_arg is either a special arg name, or a managed arg index
            if native_arg in named_args:
                native_arg_names[native_arg_pos] = named_args[native_arg]
            else:
                mgd_arg_pos = native_arg # rename for clarity
                mgd_args[mgd_arg_pos] = ic_args[mgd_arg_pos]
                native_arg_names[native_arg_pos] = _get_native_argname((mgd_arg_pos, ic_args[mgd_arg_pos]))
    else:
        mgd_args = ic_args
        native_arg_names = map(_get_native_argname, enumerate(ic_args))
    
    return mgd_args, native_arg_names

#==========================================================================

def _generate_method_signature(name, ic_ret, mgd_args):
    arglist = 'string key'
    arglist_end = generate_arglist(mgd_args, ICTYPE_2_MGDTYPE)
    if arglist_end:
        arglist = '%s, %s' % (arglist, arglist_end)
    
    return SIGNATURE_TEMPLATE % {
        'name': name,
        'arglist': arglist,
        'rettype': ICTYPE_2_MGDTYPE[ic_ret],
    }

#==========================================================================

def _generate_method_obj_translation(c_arg_types, nullable_kwargs):
    cleanups = []
    translates = []
    for (i, arg_type) in enumerate(c_arg_types):
        if arg_type == 'obj':
            template = TRANSLATE_OBJ_TEMPLATE
            if i == nullable_kwargs:
                template = TRANSLATE_NULLABLE_KWARGS_TEMPLATE
            translates.append(template % {'index': i})
            cleanups.append(CLEANUP_OBJ_TEMPLATE % {'index': i})
    return '\n'.join(translates), '\n'.join(cleanups)

#==========================================================================

def _generate_method_dgt_call(dgt_spec, callargs):
    return CALL_TEMPLATE % {
        'dgttype': dgt_spec, 
        'arglist': ', '.join(callargs)
    }

#==========================================================================

def _generate_method_ret_handling(ret_type, ret_tweak):
    if ret_type == 'void':
        return '', ret_tweak, ''
    elif ret_type == 'obj':
        return ASSIGN_RETPTR, (ret_tweak or DEFAULT_HANDLE_RETPTR), SIMPLE_RETURN
    else:
        return ASSIGN_RET_TEMPLATE % ICTYPE_2_MGDTYPE[ret_type], ret_tweak, SIMPLE_RETURN

#==========================================================================

def _generate_field(name, mgd_type, cpm_suffix, get_tweak='', set_tweak=''):
    return FIELD_TEMPLATE % {
        'name': name,
        'mgd_type': mgd_type,
        'cpm_suffix': cpm_suffix,
        'get_tweak': get_tweak,
        'set_tweak': set_tweak,
    }

#==========================================================================

class DispatcherGenerator(ApiPlumbingGenerator):
    # populates self.context.dgt_specs
    # populates self.context.dispatcher_methods
    
    RUN_INPUTS = 'DISPATCHER_FIELDS DISPATCHER_METHODS'
    def _run(self, field_types, method_types):
        dispatcher_fields = '\n\n'.join(
            starstarmap(_generate_field, field_types))
        dispatcher_methods = '\n\n'.join(
            starstarmap(self._generate_method, method_types))
        return DISPATCHER_FILE_TEMPLATE % '\n\n'.join(
            (dispatcher_fields, dispatcher_methods))


    def _generate_method(self, name, ic_spec, arg_tweak=None, ret_tweak='', nullable_kwargs=None):
        native_spec, ic_ret, ic_args = self._unpack_ic_spec(ic_spec)
        mgd_args, native_arg_names = _expand_args(ic_args, arg_tweak)
        
        self.context.dispatcher_methods[name] = (mgd_args, native_spec)
        info = {
            'signature':    _generate_method_signature(name, ic_ret, mgd_args),
            'call':         _generate_method_dgt_call(native_spec, native_arg_names),
        }
        multi_update(info, 
            ('translate_objs', 'cleanup_objs'), 
            _generate_method_obj_translation(mgd_args, nullable_kwargs)
        )
        multi_update(info, 
            ('store_ret', 'handle_ret', 'return_ret'), 
            _generate_method_ret_handling(ic_ret, ret_tweak)
        )
        return METHOD_TEMPLATE % info


