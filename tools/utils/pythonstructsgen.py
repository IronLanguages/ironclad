
from data.snippets.cs.pythonstructs import *

from tools.utils.apiplumbing import ApiPlumbingGenerator
from tools.utils.ictypes import native_ictype, VALID_ICTYPES
from tools.utils.platform import ICTYPE_2_MGDTYPE


#==========================================================================

def _generate_field_code(field_spec):
    name, ictype = field_spec
    if ictype not in VALID_ICTYPES:
        # FIXME: this is not necessarily a function ptr
        # ...but it has been in all the cases we've seen
        ictype = 'ptr'
    
    field_type = ICTYPE_2_MGDTYPE[native_ictype(ictype)]
    return STRUCT_FIELD_TEMPLATE % (field_type, name)

def _generate_struct_code(struct_spec):
    name, fields = struct_spec
    fields_code = '\n'.join(
        map(_generate_field_code, fields))
    return STRUCT_TEMPLATE % (name, fields_code)

def _generate_structs_code(struct_specs):
    return STRUCTS_FILE_TEMPLATE % '\n\n'.join(
        map(_generate_struct_code, sorted(struct_specs)))
    

#==========================================================================

class PythonStructsGenerator(ApiPlumbingGenerator):
    # no self.context dependencies
    
    RUN_INPUTS = 'MGD_API_STRUCTS'
    
    def _run(self, mgd_api_structs):
        return _generate_structs_code(mgd_api_structs)

