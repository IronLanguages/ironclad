
from tools.platform import type_codes
from tools.utils import read_interesting_lines

from data.snippets.cs.dgttype import *
from data.snippets.cs.dispatcher import *
from data.snippets.cs.magicmethods import *
from data.snippets.cs.pythonapi import *

#===============================================================================================================
# Utility functions

def starstarmap(func, items):
    for (args, kwargs) in items:
        yield func(*args, **kwargs)


def glom_templates(joiner, *args):
    output = []
    for (template, infos) in args:
        for info in infos:
            output.append(template % info)
    return joiner.join(output)


def multi_update(dict_, names, values):
    for (k, v) in zip(names, values):
        dict_[k] = v


def get_callarg((index, code)):
    if code == 'obj':
        return 'ptr%d' % index
    return 'arg%d' % index


SPECIAL_ARGS = {
    'null': NULL_ARG,
    'module': MODULE_ARG,
}

def isnormalarg(arg):
    return arg not in SPECIAL_ARGS


def unpack_args(args, argtweak):
    if not argtweak:
        return args, map(get_callarg, enumerate(args))
    else:
        callargs = [None] * len(argtweak)
        inargs = [None] * len(filter(isnormalarg, argtweak))
        for calli, callarg in enumerate(argtweak):
            if callarg in SPECIAL_ARGS:
                callargs[calli] = SPECIAL_ARGS[callarg]
            else:
                inargs[callarg] = args[callarg]
                callargs[calli] = get_callarg((callarg, args[callarg]))
        return inargs, callargs


def generate_arglist(args):
    return ', '.join('%s arg%d' % (type_codes[arg], i) for (i, arg) in enumerate(args))


def generate_signature(name, ret, inargs):
    arglist = 'string key'
    arglist_end = generate_arglist(inargs)
    if arglist_end:
        arglist = '%s, %s' % (arglist, arglist_end)
    
    return SIGNATURE_TEMPLATE % {
        'name': name,
        'arglist': arglist,
        'rettype': type_codes[ret],
    }


def generate_objs(inargs, nullablekwargs):
    cleanups = []
    translates = []
    for (i, arg) in enumerate(inargs):
        if arg == 'obj':
            template = TRANSLATE_OBJ_TEMPLATE
            if i == nullablekwargs:
                template = TRANSLATE_NULLABLEKWARGS_TEMPLATE
            translates.append(template % {'index': i})
            cleanups.append(CLEANUP_OBJ_TEMPLATE % {'index': i})
    return '\n'.join(translates), '\n'.join(cleanups)


def generate_call(dgttype, callargs):
    return CALL_TEMPLATE % {
        'dgttype': dgttype, 
        'arglist': ', '.join(callargs)
    }


def generate_ret_handling(ret, rettweak):
    if ret == 'void':
        return '', rettweak, ''
    elif ret == 'obj':
        return ASSIGN_RETPTR, (rettweak or DEFAULT_HANDLE_RETPTR), SIMPLE_RETURN
    else:
        return ASSIGN_RET_TEMPLATE % type_codes[ret], rettweak, SIMPLE_RETURN


def generate_magicmethod_template(functype, inargs, template):
    args = ', '.join(['_%d' % i for i in xrange(len(inargs))])
    return template % {
        'arglist': args,
        'callargs': args,
        'functype': functype,
    }


def generate_magicmethod_swapped_template(functype, inargs, template):
    args = ['_%d' % i for i in xrange(len(inargs))]
    return template % {
        'arglist': ', '.join(args),
        'callargs': ', '.join(args[::-1]),
        'functype': functype,
    }


def generate_dispatcher_field(name, cstype, cpmtype, gettweak='', settweak=''):
    return FIELD_TEMPLATE % {
        'name': name,
        'cstype': cstype,
        'cpmtype': cpmtype,
        'gettweak': gettweak,
        'settweak': settweak,
    }


#===============================================================================================================
# Actual code generator
#
# Note that the generator is not tested directly; however,
# the operation of the generated code is thoroughly tested
# elsewhere.

class ApiWrangler(object):

    def __init__(self, input):
        self.callmap = {}
        self.dgttypes = set()
        self.output = {}
        
        # Order of the following operations is important!
        
        self.output['dispatcher_code'] = self.generate_dispatcher(
            input['DISPATCHER_FIELDS'], 
            input['DISPATCHER_METHODS'])
            
        self.output['magicmethods_code'] = self.generate_magic_methods(
            input['MAGICMETHODS'])
            
        self.output['pythonapi_code'] = self.generate_pythonapi(
            input['MGD_API_FUNCTIONS'], 
            input['MGD_NONAPI_C_FUNCTIONS'], 
            input['ALL_API_FUNCTIONS'], 
            input['PURE_C_SYMBOLS'], 
            input['MGD_API_DATA'])
            
        self.output['dgttype_code'] = self.generate_dgts(
            input['EXTRA_DGTTYPES'])


    def _unpack_spec(self, spec):
        args = []
        dgttype = spec.replace('obj', 'ptr')
        self.dgttypes.add(dgttype)
        
        ret, argstr = spec.split('_')
        if argstr == 'void':
            return dgttype, ret, ()
        
        while len(argstr):
            for code in type_codes:
                if argstr.startswith(code):
                    args.append(code)
                    argstr = argstr[len(code):]
                    continue
        
        return dgttype, ret, tuple(args) 


    def _unpack_apifunc(self, name, dgt_type):
        _, ret, args = self._unpack_spec(dgt_type)
        return {
            "symbol": name,
            "dgt_type": dgt_type,
            "return_type": type_codes[ret],
            "arglist": generate_arglist(args)
        }


    def _generate_dgttype(self, dgttype):
        _, ret, args = self._unpack_spec(dgttype)
        return DGTTYPE_TEMPLATE % {
            'name': dgttype,
            'rettype': type_codes[ret], 
            'arglist': generate_arglist(args)
        }


    def _generate_dispatcher_method(self, name, spec, argtweak=None, rettweak='', nullablekwargs=None):
        dgttype, ret, args = self._unpack_spec(spec)
        inargs, callargs = unpack_args(args, argtweak)
        self.callmap[name] = (inargs, dgttype)
        info = {
            'signature': generate_signature(name, ret, inargs),
            'call': generate_call(dgttype, callargs),
        }
        multi_update(info, 
            ('translate_objs', 'cleanup_objs'), generate_objs(inargs, nullablekwargs))
        multi_update(info, 
            ('store_ret', 'handle_ret', 'return_ret'), generate_ret_handling(ret, rettweak))
        return METHOD_TEMPLATE % info


    def generate_pythonapi(self, mgd_pythonapi_functions, mgd_nonapi_c_functions, all_api_functions, pure_c_symbols, mgd_data):
        all_mgd_functions = mgd_pythonapi_functions | mgd_nonapi_c_functions
        not_implemented_functions = all_api_functions - pure_c_symbols
        
        methods = []
        for (name, dgt_type) in all_mgd_functions:
            if name in not_implemented_functions:
                not_implemented_functions.remove(name)
            methods.append(self._unpack_apifunc(name, dgt_type))
            
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


    def generate_dispatcher(self, field_types, method_types):
        dispatcher_fields = '\n\n'.join(starstarmap(generate_dispatcher_field, field_types))
        dispatcher_methods = '\n\n'.join(starstarmap(self._generate_dispatcher_method, method_types))
        return DISPATCHER_FILE_TEMPLATE % '\n\n'.join((dispatcher_fields, dispatcher_methods))


    def generate_magic_methods(self, protocol_field_types):
        # this depends on self.callmap having been populated (by dispatcher generation)
        normal_magic_methods = []
        swapped_magic_methods = []
        def generate_magic_method(cslotname, functype, pyslotname, swappedname=None, template=MAGICMETHOD_TEMPLATE_TEMPLATE, swappedtemplate=MAGICMETHOD_TEMPLATE_TEMPLATE):
            inargs, dgttype = self.callmap[functype]
            needswap = MAGICMETHOD_NEEDSWAP_NO
            if swappedname is not None:
                swappedtemplate = generate_magicmethod_swapped_template(functype, inargs, swappedtemplate)
                swapped_magic_methods.append(MAGICMETHOD_CASE % (cslotname, swappedname, MAGICMETHOD_NEEDSWAP_NO, dgttype, swappedtemplate))
                needswap = MAGICMETHOD_NEEDSWAP_YES
            template = generate_magicmethod_template(functype, inargs, template)
            normal_magic_methods.append(MAGICMETHOD_CASE % (cslotname, pyslotname, needswap, dgttype, template))
        
        for (args, kwargs) in protocol_field_types:
            generate_magic_method(*args, **kwargs)
        
        return MAGICMETHODS_FILE_TEMPLATE % ('\n\n'.join(normal_magic_methods), '\n\n'.join(swapped_magic_methods))
            

    def generate_dgts(self, extratypes):
        # this depends on self.dgttypes having been populated (by dispatcher and pythonapi construction)
        return FILE_TEMPLATE % '\n'.join(map(self._generate_dgttype, sorted(self.dgttypes | extratypes)))



