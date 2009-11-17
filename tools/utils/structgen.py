
from data.snippets.cs.structs import *

from tools.utils.type_codes import CTYPE_2_DGTTYPE, DGTTYPE_2_MGDTYPE

def _extract_field(field_spec):
    name, c_type = field_spec
    # anything we don't recognise is probably a typedeffed function ptr
    dgt_type = CTYPE_2_DGTTYPE.get(c_type, 'ptr')
    actual_type = DGTTYPE_2_MGDTYPE[dgt_type]
    return STRUCT_FIELD_TEMPLATE % (actual_type, name)

def generate_struct(struct_spec):
    name, fields = struct_spec
    fields_code = '\n'.join(map(_extract_field, fields))
    return STRUCT_TEMPLATE % (name, fields_code)

    
    