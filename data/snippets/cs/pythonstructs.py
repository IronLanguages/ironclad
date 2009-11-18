
from common import FILE_TEMPLATE

#================================================================================================

STRUCTS_TEMPLATE = """\
    namespace Structs
    {
%s
    }"""

STRUCTS_FILE_TEMPLATE = FILE_TEMPLATE % STRUCTS_TEMPLATE

#================================================================================================

STRUCT_TEMPLATE = """\
        [StructLayout(LayoutKind.Sequential, Pack=1)]
        public struct %s
        {
%s
        }"""

STRUCT_FIELD_TEMPLATE = """\
            public %s %s;"""