
import os, sys

from data.snippets.stub import *

from tools.utils.codegen import CodeGenerator, glom_templates, return_dict
    

#==========================================================================

def _extract_funcname(c_func):
    # hacka hacka hacka
    if '(' in c_func:
        return c_func.split('(')[0].split()[-1].replace('*', '')
    return c_func.split(';')[0].split()[-1]
    

#==========================================================================

@return_dict('symbol offset')
def _jump_info(index_name):
    (index, name) = index_name
    return name, index * 8 # assumes 64-bit adresses

def generate_jumps(functions):
    jump_infos = list(map(_jump_info, enumerate(functions)))
    return JUMPS_FILE_TEMPLATE % {
        'funccount': len(functions),
        'code': glom_templates('\n', 
            (JUMP_DECLARE_TEMPLATE, jump_infos),
            (JUMP_START_DEFINE_TEMPLATE, [{}]),
            (JUMP_DEFINE_TEMPLATE, jump_infos)),
    }

#==========================================================================

def _generate_stubinit_getfuncptr(index_name):
    (index, name) = index_name
    return STUBINIT_GETFUNCPTR_TEMPLATE % {
        'index': index,
        'symbol': name,
    }

def _generate_stubinit_registerdata(name):
    return STUBINIT_REGISTERDATA_TEMPLATE % {
        'symbol': name,
    }
    
def generate_stubinit(functions, data):
    return STUBINIT_FILE_TEMPLATE % {
        'funccount': len(functions),
        'getfuncptrs': '\n'.join(map(_generate_stubinit_getfuncptr, enumerate(functions))),
        'registerdatas': '\n'.join(map(_generate_stubinit_registerdata, data)),
    }
    

#==========================================================================

def generate_header(prototypes):
    return 'extern ' + '\nextern '.join(prototypes) + '\n'


#==========================================================================

class StubGenerator(CodeGenerator):

    INPUTS = 'EXPORTED_FUNCTIONS EXPORTED_DATA EXTRA_FUNCTIONS PURE_C_SYMBOLS MGD_API_DATA'

    def _run(self):
        needs_jump = lambda f: f not in self.PURE_C_SYMBOLS
        functions = list(filter(needs_jump, self.EXPORTED_FUNCTIONS))
        functions += list(map(_extract_funcname, self.EXTRA_FUNCTIONS))
        all_exports = set(self.EXPORTED_DATA) | set(self.EXPORTED_FUNCTIONS)
        data = filter(lambda d: d in all_exports, self.MGD_API_DATA)
        return {
            'STUBINIT':     generate_stubinit(functions, data),
            'HEADER':       generate_header(self.EXTRA_FUNCTIONS),
            'JUMPS':        generate_jumps(functions),
        }


#==========================================================================
