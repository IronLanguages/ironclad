
from .common import FILE_TEMPLATE

#================================================================================================

STRUCTS_TEMPLATE = """\
    namespace Structs
    {
%s
    }"""

STRUCTS_FILE_TEMPLATE = FILE_TEMPLATE % STRUCTS_TEMPLATE


#================================================================================================

STRUCT_TEMPLATE = """\
        [StructLayout(LayoutKind.Sequential)]
        public struct %(name)s
        {
%(fields)s
        }"""

STRUCT_FIELD_TEMPLATE = """\
            public %(type)s %(name)s;"""


#================================================================================================
