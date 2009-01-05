
from tools.platform import type_codes
from tools.dispatchersnippets import *

sideeffect_callmap = {}
sideeffect_dgttypes = set()
register_dgttype = sideeffect_dgttypes.add


def starstarmap(func, items):
    for (args, kwargs) in items:
        yield func(*args, **kwargs)


def unpack_spec(spec):
    args = []
    dgttype = spec.replace('obj', 'ptr')
    register_dgttype(dgttype)
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


def get_callarg((index, code)):
    if code == 'obj':
        return 'ptr%d' % index
    return 'arg%d' % index


def unpack_args(args, argtweak):
    if not argtweak:
        return args, map(get_callarg, enumerate(args))
    else:
        callargs = [None] * len(argtweak)
        inargs = [None] * len(filter('null'.__ne__, argtweak))
        for calli, callarg in enumerate(argtweak):
            if callarg == 'null':
                callargs[calli] = 'IntPtr.Zero'
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


def multi_update(dict_, names, values):
    for (k, v) in zip(names, values):
        dict_[k] = v        


def generate_dispatcher_method(name, spec, argtweak=None, rettweak='', nullablekwargs=None):
    dgttype, ret, args = unpack_spec(spec)
    inargs, callargs = unpack_args(args, argtweak)
    sideeffect_callmap[name] = (inargs, dgttype)
    info = {
        'signature': generate_signature(name, ret, inargs),
        'call': generate_call(dgttype, callargs),
    }
    multi_update(info, 
        ('translate_objs', 'cleanup_objs'), generate_objs(inargs, nullablekwargs))
    multi_update(info, 
        ('store_ret', 'handle_ret', 'return_ret'), generate_ret_handling(ret, rettweak))
    return METHOD_TEMPLATE % info


def generate_dispatcher_field(name, cstype, cpmtype, gettweak='', settweak=''):
    info = {
        'name': name,
        'cstype': cstype,
        'cpmtype': cpmtype,
        'gettweak': gettweak,
        'settweak': settweak,
    }
    return FIELD_TEMPLATE % info


def generate_dgttype(dgttype):
    _, ret, args = unpack_spec(dgttype)
    info = {
        'name': dgttype,
        'rettype': type_codes[ret], 
        'arglist': generate_arglist(args)
    }
    return DGTTYPE_TEMPLATE % info


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

def generate_dispatcher(field_types, method_types):
    dispatcher_fields = '\n'.join(starstarmap(generate_dispatcher_field, field_types))
    dispatcher_methods = '\n'.join(starstarmap(generate_dispatcher_method, method_types))
    return FILE_TEMPLATE % DISPATCHER_TEMPLATE % '\n\n'.join((dispatcher_fields, dispatcher_methods))

def generate_magic_methods(protocol_field_types):
    # this depends on sideeffect_callmap having been populated (by dispatcher construction)
    normal_magic_methods = []
    swapped_magic_methods = []
    def generate_magic_method(cslotname, functype, pyslotname, swapped=None, template=MAGICMETHOD_TEMPLATE_TEMPLATE, swappedtemplate=MAGICMETHOD_TEMPLATE_TEMPLATE):
        inargs, dgttype = sideeffect_callmap[functype]
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

def generate_dgts():
    # this depends on sideeffect_dgttypes having been populated (by dispatcher and python25api construction)
    return FILE_TEMPLATE % '\n'.join(map(generate_dgttype, sorted(sideeffect_dgttypes)))

#===============================================================================================================

# WARNING: the order of the following calls is important; notice the sideeffect_* variables above

from tools.dispatcherinputs import dispatcher_field_types, dispatcher_methods
dispatcher_code = generate_dispatcher(dispatcher_field_types, dispatcher_methods)

from tools.dispatcherinputs import protocol_field_types
magicmethods_code = generate_magic_methods(protocol_field_types)

# not implemented yet: would be nice, though
# from tools.typesysteminputs import python25api_functions
# python25api_code = generate_python25api(python25api_functions)

dgttype_code = generate_dgts()

if __name__ == '__main__':
    import os
    import sys
    outdir = sys.argv[1]

    def write(contents, name):
        f = open(os.path.join(outdir, name + '.Generated.cs'), 'w')
        f.write(contents)
        f.close()

    write(dispatcher_code, 'Dispatcher')
    write(magicmethods_code, 'MagicMethods')
    write(dgttype_code, 'Delegates')

