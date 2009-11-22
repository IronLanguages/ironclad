
from data.snippets.cs.magicmethods import *

from tools.utils.codegen import CodeGenerator, return_dict


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

def _generate_has_swapped_version_code(has_swapped_version):
    if has_swapped_version:
        return SWAP_YES_CODE
    return SWAP_NO_CODE

def _generate_case_code(c_field, py_field, has_swapped_version, dgt_spec, template):
    swapped_code = _generate_has_swapped_version_code(has_swapped_version)
    return MAGICMETHOD_CASE_TEMPLATE % {
        'c_field': c_field, 
        'py_field': py_field, 
        'has_swapped_version_code': swapped_code, 
        'dgt_spec': dgt_spec, 
        'template': template,
    }

#==========================================================================

class MagicMethodsGenerator(CodeGenerator):
    # requires populated self.context.dispatcher_methods

    INPUTS = 'MAGICMETHODS'
    
    @return_dict('MAGICMETHODS')
    def _run(self):
        self._normal_cases = []
        self._swapped_cases = []
        for (args, kwargs) in self.MAGICMETHODS:
            self._generate_cases(*args, **kwargs)
        
        return MAGICMETHODS_FILE_TEMPLATE % {
            'normal_cases': '\n\n'.join(self._normal_cases), 
            'swapped_cases': '\n\n'.join(self._swapped_cases)
        }
    
    def _generate_cases(self, c_field, dispatcher_method, py_field, 
            py_swapped_field=None,
            template2=MAGICMETHOD_TEMPLATE2,
            swapped_template2=MAGICMETHOD_TEMPLATE2):
        
        has_swapped_version =  py_swapped_field is not None
        mgd_args, dgt_spec = self.context.dispatcher_methods[dispatcher_method]
        
        template = _generate_normal_template(template2, dispatcher_method, mgd_args)
        self._normal_cases.append(_generate_case_code(
            c_field, py_field, has_swapped_version, dgt_spec, template))
        
        if has_swapped_version:
            swapped_template = _generate_swapped_template(swapped_template2, dispatcher_method, mgd_args)
            self._swapped_cases.append(_generate_case_code(
                c_field, py_swapped_field, False, dgt_spec, swapped_template))
    

#==========================================================================
