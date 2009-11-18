
from data.snippets.cs.pythonstructs import *

from tools.utils.apiplumbing import ApiPlumbingGenerator
from tools.utils.type_codes import ICTYPE_2_NATIVETYPE, NATIVETYPE_2_MGDTYPE


def _extract_field(field_spec):
    name, ic_type = field_spec
    # FIXME? we just assume anything we don't recognise is a typedeffed function ptr
    dgt_type = ICTYPE_2_NATIVETYPE.get(ic_type, 'ptr')
    actual_type = NATIVETYPE_2_MGDTYPE[dgt_type]
    return STRUCT_FIELD_TEMPLATE % (actual_type, name)

def _generate_struct(struct_spec):
    name, fields = struct_spec
    fields_code = '\n'.join(map(_extract_field, fields))
    return STRUCT_TEMPLATE % (name, fields_code)

def _generate_structs(struct_specs):
    return STRUCTS_FILE_TEMPLATE % '\n\n'.join(
        map(_generate_struct, sorted(struct_specs)))
    

class PythonStructsGenerator(ApiPlumbingGenerator):
    # no self.context dependencies
    
    RUN_INPUTS = 'MGD_API_STRUCTS'
    def _run(self, mgd_api_structs):
        return _generate_structs(mgd_api_structs)

