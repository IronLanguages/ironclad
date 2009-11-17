
from data.snippets.cs.structs import *

from tools.utils.type_codes import ICTYPE_2_NATIVETYPE, NATIVETYPE_2_MGDTYPE

def _extract_field(field_spec):
    name, ic_type = field_spec
    # FIXME? assume anything we don't recognise is a typedeffed function ptr
    dgt_type = ICTYPE_2_NATIVETYPE.get(ic_type, 'ptr')
    actual_type = NATIVETYPE_2_MGDTYPE[dgt_type]
    return STRUCT_FIELD_TEMPLATE % (actual_type, name)

def generate_struct(struct_spec):
    name, fields = struct_spec
    fields_code = '\n'.join(map(_extract_field, fields))
    return STRUCT_TEMPLATE % (name, fields_code)

    
    