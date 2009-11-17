
from data.snippets.cs.dispatcher import *

from tools.utils.type_codes import CTYPE_2_MGDTYPE
from tools.utils.codegen import generate_arglist

#===============================================
# expand_args

def _get_dgt_argname((index, code)):
    return {'obj': 'ptr%d'}.get(code, 'arg%d') % index

SPECIAL_DISPATCHER_ARG_NAMES = {
    'null': NULL_ARG,
    'module': MODULE_ARG,
}

def _is_normal_arg(arg):
    return arg not in SPECIAL_DISPATCHER_ARG_NAMES

def expand_args(c_arg_types, argtweak=None):
    if not argtweak:
        mgd_arg_types = c_arg_types
        dgt_arg_names = map(_get_dgt_argname, enumerate(c_arg_types))
    else:
        named_args = SPECIAL_DISPATCHER_ARG_NAMES
        mgd_arg_types = [None] * len(filter(_is_normal_arg, argtweak))
        dgt_arg_names = [None] * len(argtweak)
        
        for dgt_arg_pos, dgt_arg in enumerate(argtweak):
            # NOTE: dgt_arg is either a special arg name, or a managed arg index
            if dgt_arg in named_args:
                dgt_arg_names[dgt_arg_pos] = named_args[dgt_arg]
            else:
                mgd_arg_pos = dgt_arg # rename for clarity
                mgd_arg_types[mgd_arg_pos] = c_arg_types[mgd_arg_pos]
                dgt_arg_names[dgt_arg_pos] = _get_dgt_argname((mgd_arg_pos, c_arg_types[mgd_arg_pos]))
    
    return mgd_arg_types, dgt_arg_names

#===============================================

def method_signature(name, ret_type, arg_types):
    arglist = 'string key'
    arglist_end = generate_arglist(arg_types, CTYPE_2_MGDTYPE)
    if arglist_end:
        arglist = '%s, %s' % (arglist, arglist_end)
    
    return SIGNATURE_TEMPLATE % {
        'name': name,
        'arglist': arglist,
        'rettype': CTYPE_2_MGDTYPE[ret_type],
    }


#===============================================

def method_obj_translation(c_arg_types, nullablekwargs):
    cleanups = []
    translates = []
    for (i, arg_type) in enumerate(c_arg_types):
        if arg_type == 'obj':
            template = TRANSLATE_OBJ_TEMPLATE
            if i == nullablekwargs:
                template = TRANSLATE_NULLABLEKWARGS_TEMPLATE
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

def method_ret_handling(ret_type, rettweak):
    if ret_type == 'void':
        return '', rettweak, ''
    elif ret_type == 'obj':
        return ASSIGN_RETPTR, (rettweak or DEFAULT_HANDLE_RETPTR), SIMPLE_RETURN
    else:
        return ASSIGN_RET_TEMPLATE % CTYPE_2_MGDTYPE[ret_type], rettweak, SIMPLE_RETURN


#===============================================

def field(name, cstype, cpmtype, gettweak='', settweak=''):
    return FIELD_TEMPLATE % {
        'name': name,
        'cstype': cstype,
        'cpmtype': cpmtype,
        'gettweak': gettweak,
        'settweak': settweak,
    }