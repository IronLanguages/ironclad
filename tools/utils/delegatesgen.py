
from data.snippets.cs.delegates import *

from tools.utils.codegen import CodeGenerator, return_dict


#==========================================================================

def _generate_delegate_code(spec):
    return DELEGATE_TEMPLATE % {
        'name': spec,
        'rettype': spec.mgd_ret, 
        'arglist': spec.mgd_arglist,
    }


#==========================================================================

class DelegatesGenerator(CodeGenerator):
    # requires populated self.context.dgt_specs

    @return_dict('DELEGATES')
    def _run(self):
        return DELEGATES_FILE_TEMPLATE % '\n\n'.join(
            map(_generate_delegate_code, self.context.dgt_specs))

#==========================================================================
