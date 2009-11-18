
from common import FILE_TEMPLATE

#================================================================================================

DGTTYPE_TEMPLATE = """\
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate %(rettype)s dgt_%(name)s(%(arglist)s);
"""

DELEGATES_FILE_TEMPLATE = FILE_TEMPLATE