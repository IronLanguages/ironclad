
import os
from itertools import starmap

from data.snippets.cs.codesnippets import *

from tools.utils.codegen import CodeGenerator, return_dict


#==========================================================================

def _generate_codesnippet(name, contents):
    return CODESNIPPET_TEMPLATE % {
        'name': name, 
        'code': contents.replace('"', '""'),
    }


#==========================================================================

class CodeSnippetsGenerator(CodeGenerator):
    
    INPUTS = 'ALL_FILES'

    @return_dict('CODESNIPPETS')
    def _run(self):
        return CODESNIPPETS_FILE_TEMPLATE % '\n\n'.join(
            starmap(_generate_codesnippet, self.ALL_FILES))


#==========================================================================
