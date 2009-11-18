
from data.snippets.cs.delegates import *

from tools.utils.apiplumbing import ApiPlumbingGenerator
from tools.utils.codegen import generate_arglist, unpack_spec
from tools.utils.type_codes import NATIVETYPES, NATIVETYPE_2_MGDTYPE


def _generate_dgt_type(native_spec):
    native_ret, native_args = unpack_spec(native_spec, NATIVETYPES)
    return DGTTYPE_TEMPLATE % {
        'name': native_spec,
        'rettype': NATIVETYPE_2_MGDTYPE[native_ret], 
        'arglist': generate_arglist(native_args, NATIVETYPE_2_MGDTYPE)
    }


class DelegatesGenerator(ApiPlumbingGenerator):
    # requires populated self.context.dgt_specs

    def _run(self):
        dgt_types = '\n'.join(map(_generate_dgt_type, sorted(self.context.dgt_specs)))
        return DELEGATES_FILE_TEMPLATE % dgt_types

