
using System;
using System.Runtime.InteropServices;


namespace Ironclad
{
    namespace Structs
    {
        [Flags]
        public enum METH : uint
        {
            OLDARGS = 0,
            VARARGS = 0x00000001,
            KEYWORDS = 0x00000002,
            NOARGS = 0x00000004,
            O = 0x00000008,
            CLASS = 0x00000010,
            STATIC = 0x00000020,
            COEXIST = 0x00000040,
        }
        
        [Flags]
        public enum Py_TPFLAGS : uint
        {
            HAVE_GETCHARBUFFER = 0x00000001,
            HAVE_SEQUENCE_IN = 0x00000002,
            HAVE_INPLACEOPS = 0x00000008,
            CHECKTYPES = 0x00000010,
            HAVE_RICHCOMPARE = 0x00000020,
            HAVE_WEAKREFS = 0x00000040,
            HAVE_ITER = 0x00000080,
            HAVE_CLASS = 0x00000100,
            HEAPTYPE = 0x00000200,
            BASETYPE = 0x00000400,
            READY = 0x00001000,
            READYING = 0x00002000,
            HAVE_GC = 0x00004000,
            HAVE_INDEX = 0x00020000,
            HAVE_VERSION_TAG = 0x00040000,
            VALID_VERSION_TAG = 0x00080000,
            IS_ABSTRACT = 0x00100000,
            HAVE_NEWBUFFER = 0x00200000,
            INT_SUBCLASS = 0x00800000,
            LONG_SUBCLASS = 0x01000000,
            LIST_SUBCLASS = 0x02000000,
            TUPLE_SUBCLASS = 0x04000000,
            STRING_SUBCLASS = 0x08000000,
            UNICODE_SUBCLASS = 0x10000000,
            DICT_SUBCLASS = 0x20000000,
            BASE_EXC_SUBCLASS = 0x40000000,
            TYPE_SUBCLASS = 0x80000000,
        }
                
        public enum CMP : uint
        {
            Py_LT = 0,
            Py_LE = 1,
            Py_EQ = 2,
            Py_NE = 3,
            Py_GT = 4,
            Py_GE = 5,
        }
        
        public enum EvalToken
        {
            Py_single_input = 256,
            Py_file_input = 257,
            Py_eval_input = 258,
        }
        
        public enum MemberT
        {
            SHORT = 0,
            INT = 1,
            LONG = 2,
            FLOAT = 3,
            DOUBLE = 4,
            STRING = 5,
            OBJECT = 6,
            CHAR = 7,
            BYTE = 8,
            UBYTE = 9,
            USHORT = 10,
            UINT = 11,
            ULONG = 12,
            STRING_INPLACE = 13,
            OBJECT_EX = 16,
            LONGLONG = 17,
            ULONGLONG = 18,
        }
    }
}


