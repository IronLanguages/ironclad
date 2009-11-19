
from data.snippets.cs.magicmethods import *

from tools.utils.apiplumbing import ApiPlumbingGenerator


#==========================================================================

def _generate_template(template2, functype, inargs, callargs):
    return template2 % {
        'functype': functype,
        'arglist': ', '.join(inargs),
        'callargs': ', '.join(callargs),
    }

def _generate_normal_template(template2, functype, inargs):
    args = ['_%d' % i for i in xrange(len(inargs))]
    return _generate_template(template2, functype, args, args)

def _generate_swapped_template(template2, functype, inargs):
    args = ['_%d' % i for i in xrange(len(inargs))]
    return _generate_template(template2, functype, args, args[::-1])


#==========================================================================

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
            swapped_template = _generate_swapped_template(swapped_template2, dispatcher_method_name, mgd_args)
            self._swapped_magicmethods.append(MAGICMETHOD_CASE % (
                c_field_name, py_swapped_field_name, MAGICMETHOD_NEEDSWAP_NO, native_spec, swapped_template))
        
        template = _generate_normal_template(template2, dispatcher_method_name, mgd_args)
        self._normal_magicmethods.append(MAGICMETHOD_CASE % (
            c_field_name, py_field_name, needswap, native_spec, template))

