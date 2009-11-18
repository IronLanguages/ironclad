
from data.snippets.cs.magicmethods import *

from tools.utils.apiplumbing import ApiPlumbingGenerator


def _normal_template(functype, inargs, template):
    args = ', '.join(['_%d' % i for i in xrange(len(inargs))])
    return template % {
        'arglist': args,
        'callargs': args,
        'functype': functype,
    }

def _swapped_template(functype, inargs, template):
    args = ['_%d' % i for i in xrange(len(inargs))]
    return template % {
        'arglist': ', '.join(args),
        'callargs': ', '.join(args[::-1]),
        'functype': functype,
    }


class MagicMethodsGenerator(ApiPlumbingGenerator):
    # requires populated self.context.dispatcher_methods

    RUN_INPUTS = 'MAGICMETHODS'
    def _run(self, magicmethods_info):
        self._normal_magicmethods = []
        self._swapped_magicmethods = []
        
        for (args, kwargs) in magicmethods_info:
            self._generate_magicmethod(*args, **kwargs)
        
        return MAGICMETHODS_FILE_TEMPLATE % (
            '\n\n'.join(self._normal_magicmethods), 
            '\n\n'.join(self._swapped_magicmethods))
    
    
    def _generate_magicmethod(self, c_field_name, dispatcher_method_name, py_field_name, 
            py_swapped_field_name=None,
            template2=MAGICMETHOD_TEMPLATE_TEMPLATE,
            swapped_template2=MAGICMETHOD_TEMPLATE_TEMPLATE):
        
        mgd_args, native_spec = self.context.dispatcher_methods[dispatcher_method_name]
        needswap = MAGICMETHOD_NEEDSWAP_NO
        
        if py_swapped_field_name is not None:
            needswap = MAGICMETHOD_NEEDSWAP_YES
            swapped_template = _swapped_template(dispatcher_method_name, mgd_args, swapped_template2)
            self._swapped_magicmethods.append(MAGICMETHOD_CASE % (
                c_field_name, py_swapped_field_name, MAGICMETHOD_NEEDSWAP_NO, native_spec, swapped_template))
        
        template = _normal_template(dispatcher_method_name, mgd_args, template2)
        self._normal_magicmethods.append(MAGICMETHOD_CASE % (
            c_field_name, py_field_name, needswap, native_spec, template))

