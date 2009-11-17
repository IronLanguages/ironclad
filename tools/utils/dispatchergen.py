
from data.snippets.cs.dispatcher import *

from tools.utils.type_codes import ICTYPE_2_MGDTYPE
from tools.utils.codegen import generate_arglist

#===============================================
# expand_args

def _get_native_argname((index, code)):
    return {'obj': 'ptr%d'}.get(code, 'arg%d') % index

SPECIAL_DISPATCHER_ARG_NAMES = {
    'null': NULL_ARG,
    'module': MODULE_ARG,
}

def _is_normal_arg(arg):
    return arg not in SPECIAL_DISPATCHER_ARG_NAMES

def expand_args(ic_args, arg_tweak=None):
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

#===============================================

def method_signature(name, ic_ret, mgd_args):
    arglist = 'string key'
    arglist_end = generate_arglist(mgd_args, ICTYPE_2_MGDTYPE)
    if arglist_end:
        arglist = '%s, %s' % (arglist, arglist_end)
    
    return SIGNATURE_TEMPLATE % {
        'name': name,
        'arglist': arglist,
        'rettype': ICTYPE_2_MGDTYPE[ic_ret],
    }


#===============================================

def method_obj_translation(c_arg_types, nullable_kwargs):
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


#===============================================

def method_dgt_call(dgt_spec, callargs):
    return CALL_TEMPLATE % {
        'dgttype': dgt_spec, 
        'arglist': ', '.join(callargs)
    }


#===============================================

def method_ret_handling(ret_type, ret_tweak):
    if ret_type == 'void':
        return '', ret_tweak, ''
    elif ret_type == 'obj':
        return ASSIGN_RETPTR, (ret_tweak or DEFAULT_HANDLE_RETPTR), SIMPLE_RETURN
    else:
        return ASSIGN_RET_TEMPLATE % ICTYPE_2_MGDTYPE[ret_type], ret_tweak, SIMPLE_RETURN


#===============================================

def field(name, mgd_type, cpm_suffix, get_tweak='', set_tweak=''):
    return FIELD_TEMPLATE % {
        'name': name,
        'mgd_type': mgd_type,
        'cpm_suffix': cpm_suffix,
        'get_tweak': get_tweak,
        'set_tweak': set_tweak,
    }