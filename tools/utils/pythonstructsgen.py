
from data.snippets.cs.pythonstructs import *

from tools.utils.codegen import CodeGenerator, return_dict
from tools.utils.ictypes import native_ictype, VALID_ICTYPES
from tools.utils.gccxml import get_structspecs, in_set
from tools.utils.platform import ICTYPE_2_MGDTYPE


#==========================================================================

def _generate_field_code(fieldspec):
    name, ictype = fieldspec
    if ictype not in VALID_ICTYPES:
        # FIXME: this is not necessarily a function ptr
        # ...but it has been in all the cases we've seen
        ictype = 'ptr'
    
    return STRUCT_FIELD_TEMPLATE % {
        'name': name,
        'type': ICTYPE_2_MGDTYPE[native_ictype(ictype)], 
    }

def _generate_struct_code(structspec):
    name, fields = structspec
    fields_code = '\n'.join(
        map(_generate_field_code, fields))
    return STRUCT_TEMPLATE % {
        'name': name, 
        'fields': fields_code
    }
    

#==========================================================================

class PythonStructsGenerator(CodeGenerator):
    # no self.context dependencies
    
    INPUTS = 'MGD_API_STRUCTS STUBMAIN'
    
    @return_dict('PythonStructs.Generated.cs')
    def _run(self):
        structspecs = get_structspecs(
            self.STUBMAIN.classes(in_set(self.MGD_API_STRUCTS)),
            self.STUBMAIN.typedefs(in_set(self.MGD_API_STRUCTS)))
        
        return STRUCTS_FILE_TEMPLATE % '\n\n'.join(
            map(_generate_struct_code, sorted(structspecs)))
    

#==========================================================================
