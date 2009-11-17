
from data.snippets.cs.dgttype import *

from tools.utils.codegen import generate_arglist, unpack_spec
from tools.utils.type_codes import NATIVETYPES, NATIVETYPE_2_MGDTYPE


def generate_dgttype(native_spec):
    native_ret, native_args = unpack_spec(native_spec, NATIVETYPES)
    return DGTTYPE_TEMPLATE % {
        'name': native_spec,
        'rettype': NATIVETYPE_2_MGDTYPE[native_ret], 
        'arglist': generate_arglist(native_args, NATIVETYPE_2_MGDTYPE)
    }


