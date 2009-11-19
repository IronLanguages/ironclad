
from data.snippets.cs.dispatcher import *

from tools.utils.apiplumbing import ApiPlumbingGenerator
from tools.utils.gccxml import get_funcspecs, equal
from tools.utils.ictypes import ICTYPE_2_MGDTYPE


#==========================================================================

def _starstarmap(func, items):
    for (args, kwargs) in items:
        yield func(*args, **kwargs)

def _multi_update(dict_, names, values):
    for (name, value) in zip(names, values):
        dict_[name] = value


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

def _generate_signature_code(name, spec):
    arglist = '%s key' % ICTYPE_2_MGDTYPE['str']
    arglist_rest = spec.mgd_arglist
    if arglist_rest:
        arglist = ', '.join((arglist, arglist_rest))
    
    return SIGNATURE_TEMPLATE % {
        'name': name,
        'arglist': arglist,
        'rettype': spec.mgd_ret,
    }


#==========================================================================

def _generate_translate_cleanup_code(args, nullable_kwargs_index):
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

def _generate_call_dgt_code(spec, arg_names):
    return CALL_DGT_TEMPLATE % {
        'spec': spec, 
        'arglist': ', '.join(arg_names)
    }


#==========================================================================

def _generate_ret_handling_code(spec, ret_tweak):
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

class DispatcherGenerator(ApiPlumbingGenerator):
    # populates self.context.dgt_specs
    # populates self.context.dispatcher_methods
    
    INPUTS = 'DISPATCHER_FIELDS DISPATCHER_METHODS GCCXML'
    
    def _run(self):
        dispatcher_fields_code = '\n\n'.join(
            _starstarmap(_generate_field_code, self.DISPATCHER_FIELDS))
        
        dispatcher_methods_code = '\n\n'.join(
            _starstarmap(self._generate_method_code, self.DISPATCHER_METHODS))
        
        return DISPATCHER_FILE_TEMPLATE % '\n\n'.join(
            (dispatcher_fields_code, dispatcher_methods_code))

    def _get_spec(self, name):
        _, spec = get_funcspecs(
            self.GCCXML.typedefs(equal(name))).pop()
        return spec

    def _generate_method_code(self, name, spec_from=None, arg_tweak=None, ret_tweak='', nullable_kwargs_index=None):
        base = self._get_spec(spec_from or name)
        native = base.native
        self.context.dgt_specs.add(native)
        
        mgd_args, native_arg_names = _tweak_args(base.args, arg_tweak)
        mgd = base.withargs(mgd_args)
        self.context.dispatcher_methods[name] = (mgd.args, native)
        
        info = {
            'signature':    _generate_signature_code(name, mgd),
            'call_dgt':     _generate_call_dgt_code(native, native_arg_names),
        }
        _multi_update(info, 
            ('translate_objs', 'cleanup_objs'), 
            _generate_translate_cleanup_code(mgd.args, nullable_kwargs_index)
        )
        _multi_update(info, 
            ('store_ret', 'handle_ret', 'return_ret'), 
            _generate_ret_handling_code(base, ret_tweak)
        )
        return METHOD_TEMPLATE % info


