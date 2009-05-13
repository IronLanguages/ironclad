
import os

from tools.platform import type_codes
from tools.dispatchersnippets import *


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


def read_interesting_lines(name):
    f = open(name)
    try:
        return [l.rstrip() for l in f.readlines() if l.rstrip()]
    finally:
        f.close() 

#===============================================================================================================


def get_callarg((index, code)):
    if code == 'obj':
        return 'ptr%d' % index
    return 'arg%d' % index


def isnormalarg(arg):
    return arg not in ('null', 'module')


def unpack_args(args, argtweak):
    if not argtweak:
        return args, map(get_callarg, enumerate(args))
    else:
        callargs = [None] * len(argtweak)
        inargs = [None] * len(filter(isnormalarg, argtweak))
        for calli, callarg in enumerate(argtweak):
            if callarg == 'null':
                callargs[calli] = 'IntPtr.Zero'
            elif callarg == 'module':
                callargs[calli] = 'this.modulePtr'
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
    info = {
        'name': name,
        'arglist': arglist,
        'rettype': type_codes[ret],
    }
    return SIGNATURE_TEMPLATE % info


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
    info = {
        'dgttype': dgttype, 
        'arglist': ', '.join(callargs)
    }
    return CALL_TEMPLATE % info


def generate_ret_handling(ret, rettweak):
    if ret == 'void':
        return '', rettweak, ''
    elif ret == 'obj':
        return 'IntPtr retptr = ', (rettweak or DEFAULT_HANDLE_RETPTR), 'return ret;'
    else:
        return '%s ret = ' % type_codes[ret], rettweak, 'return ret;'


def generate_magicmethod_template(functype, inargs, template):
    args = ', '.join(['_%d' % i for i in xrange(len(inargs))])
    info = {
        'arglist': args,
        'callargs': args,
        'functype': functype,
    }
    return template % info

def generate_magicmethod_swapped_template(functype, inargs, template):
    args = ['_%d' % i for i in xrange(len(inargs))]
    info = {
        'arglist': ', '.join(args),
        'callargs': ', '.join(args[::-1]),
        'functype': functype,
    }
    return template % info


def generate_dispatcher_field(name, cstype, cpmtype, gettweak='', settweak=''):
    info = {
        'name': name,
        'cstype': cstype,
        'cpmtype': cpmtype,
        'gettweak': gettweak,
        'settweak': settweak,
    }
    return FIELD_TEMPLATE % info


#===============================================================================================================

class ApiWrangler(object):

    def __init__(self, **input):
        self.callmap = {}
        self.dgttypes = set()
        self.output = {}
        
        self.output['dispatcher_code'] = self.generate_dispatcher(
            input['dispatcher_field_types'], 
            input['dispatcher_methods'])
        
        self.output['magicmethods_code'] = self.generate_magic_methods(
            input['protocol_field_types'])
        
        self.output['python25api_code'] = self.generate_python25api(
            input['known_python25api_signatures'], 
            input['all_functions_file'], 
            input['c_functions_file'], 
            input['data_items_file'])

        self.output['dgttype_code'] = self.generate_dgts()


    def unpack_spec(self, spec):
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


    def unpack_apifunc(self, name, dgt_type):
        _, ret, args = self.unpack_spec(dgt_type)
        return {
            "symbol": name,
            "dgt_type": dgt_type,
            "return_type": type_codes[ret],
            "arglist": generate_arglist(args)
        }


    def generate_dgttype(self, dgttype):
        _, ret, args = self.unpack_spec(dgttype)
        info = {
            'name': dgttype,
            'rettype': type_codes[ret], 
            'arglist': generate_arglist(args)
        }
        return DGTTYPE_TEMPLATE % info


    def generate_dispatcher_method(self, name, spec, argtweak=None, rettweak='', nullablekwargs=None):
        dgttype, ret, args = self.unpack_spec(spec)
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


    def generate_dispatcher(self, field_types, method_types):
        dispatcher_fields = '\n'.join(starstarmap(generate_dispatcher_field, field_types))
        dispatcher_methods = '\n'.join(starstarmap(self.generate_dispatcher_method, method_types))
        return FILE_TEMPLATE % DISPATCHER_TEMPLATE % '\n\n'.join((dispatcher_fields, dispatcher_methods))


    def generate_magic_methods(self, protocol_field_types):
        # this depends on self.callmap having been populated (by dispatcher generation)
        normal_magic_methods = []
        swapped_magic_methods = []
        def generate_magic_method(cslotname, functype, pyslotname, swapped=None, template=MAGICMETHOD_TEMPLATE_TEMPLATE, swappedtemplate=MAGICMETHOD_TEMPLATE_TEMPLATE):
            inargs, dgttype = self.callmap[functype]
            needswap = ''
            if swapped:
                needswap = 'needGetSwappedInfo = true;'
            template = generate_magicmethod_template(functype, inargs, template)
            normal_magic_methods.append(MAGIC_METHOD_CASE % (cslotname, pyslotname, template, dgttype, needswap))
            if not swapped:
                return
            swappedtemplate = generate_magicmethod_swapped_template(functype, inargs, swappedtemplate)
            swapped_magic_methods.append(MAGIC_METHOD_CASE % (cslotname, swapped, swappedtemplate, dgttype, ''))
        
        for (args, kwargs) in protocol_field_types:
            generate_magic_method(*args, **kwargs)
        
        return FILE_TEMPLATE % MAGICMETHODS_TEMPLATE % ('\n'.join(normal_magic_methods), '\n'.join(swapped_magic_methods))


    def generate_python25api(self, known_functions, all_functions_file, c_functions_file, data_items_file):
        all_methods_set = set(read_interesting_lines(all_functions_file))
        c_methods_set = set(read_interesting_lines(c_functions_file))
        not_implemented_methods_set = all_methods_set - c_methods_set
        
        methods = []
        for (name, dgt_type) in known_functions:
            not_implemented_methods_set.remove(name)
            methods.append(self.unpack_apifunc(name, dgt_type))
        not_implemented_methods = [{"symbol": s} for s in not_implemented_methods_set]
        methods_code = glom_templates('\n\n',
            (PYTHON25API_METHOD_TEMPLATE, methods), 
            (PYTHON25API_NOT_IMPLEMENTED_METHOD_TEMPLATE, not_implemented_methods),
        )
        methods_switch = glom_templates('\n',
            (PYTHON25API_METHOD_CASE, methods),
            (PYTHON25API_NOT_IMPLEMENTED_METHOD_CASE, not_implemented_methods),
        )

        data_items = []
        for p in read_interesting_lines(data_items_file):
            symbol, _type = p.split(" ")
            data_items.append({"symbol": symbol, "type": _type})
        data_items_code = glom_templates("\n\n", (PYTHON25API_DATA_ITEM_TEMPLATE, data_items))
        data_items_switch = glom_templates("\n", (PYTHON25API_DATA_ITEM_CASE, data_items))

        return FILE_TEMPLATE % PYTHON25API_TEMPLATE % (
            methods_code, methods_switch,
            data_items_code, data_items_switch)
            

    def generate_dgts(self):
        # this depends on self.dgttypes having been populated (by dispatcher and python25api construction)
        return FILE_TEMPLATE % '\n'.join(map(self.generate_dgttype, sorted(self.dgttypes)))


if __name__ == '__main__':
    import os
    import sys
    outdir = sys.argv[1]
    
    from tools.dispatcherinputs import WRANGLER_INPUT
    wrangler = ApiWrangler(**WRANGLER_INPUT)

    def write(key, name):
        f = open(os.path.join(outdir, name + '.Generated.cs'), 'w')
        f.write("/* This file was generated by tools/generatedispatcher.py */\n")
        f.write(wrangler.output[key])
        f.close()

    write('magicmethods_code', 'MagicMethods')
    write('python25api_code', 'Python25Api')
    write('dispatcher_code', 'Dispatcher')
    write('dgttype_code', 'Delegates')

