
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
def _jump_info((index, name)):
    return name, index * 4 # FIXME: 32-bit

def generate_jumps(functions):
    jump_infos = map(_jump_info, enumerate(functions))
    return JUMPS_FILE_TEMPLATE % glom_templates('\n', 
        (JUMP_DECLARE_TEMPLATE, jump_infos),
        (JUMP_DEFINE_TEMPLATE, jump_infos))
    

#==========================================================================

def _generate_stubinit_getfuncptr((index, name)):
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
    return '\n'.join(prototypes) + '\n'


#==========================================================================

class StubGenerator(CodeGenerator):

    INPUTS = 'EXPORTED_FUNCTIONS EXTRA_FUNCTIONS PURE_C_SYMBOLS MGD_API_DATA'

    def _run(self):
        needs_jump = lambda f: f not in self.PURE_C_SYMBOLS
        functions = filter(needs_jump, self.EXPORTED_FUNCTIONS)
        functions += map(_extract_funcname, self.EXTRA_FUNCTIONS)
        return {
            'STUBINIT':     generate_stubinit(functions, self.MGD_API_DATA),
            'HEADER':       generate_header(self.EXTRA_FUNCTIONS),
            'JUMPS':        generate_jumps(functions),
        }


#==========================================================================
