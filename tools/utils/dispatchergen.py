
from itertools import chain

from data.snippets.cs.dispatcher import *

from tools.utils.codegen import CodeGenerator, return_dict, starstarmap
from tools.utils.gccxml import get_funcspecs, equal
from tools.utils.ictypes import ICTYPE_2_MGDTYPE


#==========================================================================

def _native_argname((index, ictype)):
    return {'obj': 'ptr%d'}.get(ictype, 'arg%d') % index

_SPECIAL_ARGS = {
    'null': NULL_ARG,
    'module': MODULE_ARG,
}

def _tweak_args(base_mgd_args, arg_tweak=None):
    if arg_tweak is None:
        return base_mgd_args, map(_native_argname, enumerate(base_mgd_args))
    
    mgd_arg_count = len([a for a in arg_tweak if a not in _SPECIAL_ARGS])
    mgd_args = [None] * mgd_arg_count
    
    native_arg_count = len(arg_tweak)
    native_arg_names = [None] * native_arg_count
    
    for native_arg_pos, mgd_arg_id in enumerate(arg_tweak):
        if mgd_arg_id in _SPECIAL_ARGS:
            native_arg_names[native_arg_pos] = _SPECIAL_ARGS[mgd_arg_id]
        else:
            mgd_arg = base_mgd_args[mgd_arg_id]
            mgd_args[mgd_arg_id] = mgd_arg
            native_arg_names[native_arg_pos] = _native_argname((mgd_arg_id, mgd_arg))

    return mgd_args, native_arg_names


#==========================================================================

def _get_mgd_arglist(spec):
    arglist = '%s key' % ICTYPE_2_MGDTYPE['str']
    arglist_rest = spec.mgd_arglist
    if arglist_rest:
        arglist = ', '.join((arglist, arglist_rest))
    return arglist

def _generate_signature_snippet(name, spec):
    return SIGNATURE_TEMPLATE % {
        'name': name,
        'rettype': spec.mgd_ret,
        'arglist': _get_mgd_arglist(spec),
    }


#==========================================================================

@return_dict('translate_objs cleanup_objs')
def _generate_translate_snippets(args, nullable_kwargs_index):
    cleanups = []
    translates = []
    for (i, arg) in enumerate(args):
        if arg == 'obj':
            translate_template = TRANSLATE_OBJ_TEMPLATE
            if i == nullable_kwargs_index:
                translate_template = TRANSLATE_NULLABLE_KWARGS_TEMPLATE
            translates.append(translate_template % {'index': i})
            cleanups.append(CLEANUP_OBJ_TEMPLATE % {'index': i})
    return '\n'.join(translates), '\n'.join(cleanups)


#==========================================================================

def _generate_call_dgt_snippet(spec, arg_names):
    return CALL_DGT_TEMPLATE % {
        'spec': spec, 
        'arglist': ', '.join(arg_names)
    }


#==========================================================================

@return_dict('assign_ret handle_ret return_ret')
def _generate_ret_snippets(spec, ret_tweak):
    if spec.ret == 'void':
        return '', ret_tweak, ''
    elif spec.ret == 'obj':
        return ASSIGN_RETPTR, (ret_tweak or DEFAULT_HANDLE_RETPTR), SIMPLE_RETURN
    else:
        return ASSIGN_RET_TEMPLATE % spec.mgd_ret, ret_tweak, SIMPLE_RETURN


#==========================================================================

def _generate_field_code(name, mgd_type, cpm_suffix, get_tweak='', set_tweak=''):
    return FIELD_TEMPLATE % {
        'name': name,
        'mgd_type': mgd_type,
        'cpm_suffix': cpm_suffix,
        'get_tweak': get_tweak,
        'set_tweak': set_tweak,
    }


#==========================================================================

class DispatcherGenerator(CodeGenerator):
    # populates self.context.dgt_specs
    # populates self.context.dispatcher_methods
    
    INPUTS = 'DISPATCHER_FIELDS DISPATCHER_METHODS STUBMAIN'
    
    @return_dict('DISPATCHER')
    def _run(self):
        return DISPATCHER_FILE_TEMPLATE % '\n\n'.join(chain(
            starstarmap(_generate_field_code, self.DISPATCHER_FIELDS),
            starstarmap(self._generate_method_code, self.DISPATCHER_METHODS)))

    def _get_spec(self, name):
        _, spec = get_funcspecs(
            self.STUBMAIN.typedefs(equal(name))).pop()
        return spec

    def _generate_method_code(self, name,
            spec_from=None, 
            arg_tweak=None, 
            ret_tweak='', 
            nullable_kwargs_index=None):
        
        base = self._get_spec(spec_from or name)
        native = base.native
        self.context.dgt_specs.add(native)
        
        mgd_args, native_arg_names = _tweak_args(base.args, arg_tweak)
        mgd = base.withargs(mgd_args)
        self.context.dispatcher_methods[name] = (mgd.args, native)
        
        info = {
            'signature':    _generate_signature_snippet(name, mgd),
            'call_dgt':     _generate_call_dgt_snippet(native, native_arg_names),
        }
        info.update(_generate_translate_snippets(mgd.args, nullable_kwargs_index))
        info.update(_generate_ret_snippets(base, ret_tweak))
        
        return METHOD_TEMPLATE % info
    

#==========================================================================
