
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
        
        [StructLayout(LayoutKind.Sequential, Pack=1)]
        public struct PyMethodDef
        {
            public string ml_name;
            public IntPtr ml_meth;
            public METH ml_flags;
            public string ml_doc;

            public PyMethodDef(string name, IntPtr meth, METH flags, string doc)
            {
                this.ml_name = name;
                this.ml_meth = meth;
                this.ml_flags = flags;
                this.ml_doc = doc;
            }
        }
        
        [StructLayout(LayoutKind.Sequential, Pack=1)]
        public struct PyGetSetDef
        {
            public string name;
            public IntPtr get;
            public IntPtr set;
            public string doc;
            public IntPtr closure;

            public PyGetSetDef(string name, IntPtr get, IntPtr set, string doc, IntPtr closure)
            {
                this.name = name;
                this.get = get;
                this.set = set;
                this.doc = doc;
                this.closure = closure;
            }
        }
        
        [StructLayout(LayoutKind.Sequential, Pack=1)]
        public struct PyMemberDef
        {
            public string name;
            public MemberT type;
            public int offset;
            public int flags;
            public string doc;

            public PyMemberDef(string name, MemberT type, int offset, int flags, string doc)
            {
                this.name = name;
                this.type = type;
                this.offset = offset;
                this.flags = flags;
                this.doc = doc;
            }
        }
        
        [StructLayout(LayoutKind.Sequential, Pack=1)]
        public struct Py_complex
        {
            public double real;
            public double imag;

            public Py_complex(double real_, double imag_)
            {
                this.real = real_;
                this.imag = imag_;
            }
        }
        
        [StructLayout(LayoutKind.Sequential, Pack=1)]
        public struct PyObject
        {
            public uint ob_refcnt;
            public IntPtr ob_type;
        }

        [StructLayout(LayoutKind.Sequential, Pack = 1)]
        public struct PyIntObject
        {
            public uint ob_refcnt;
            public IntPtr ob_type;
            public int ob_ival;
        }

        [StructLayout(LayoutKind.Sequential, Pack = 1)]
        public struct PyFloatObject
        {
            public uint ob_refcnt;
            public IntPtr ob_type;
            public double ob_fval;
        }
        
        [StructLayout(LayoutKind.Sequential, Pack=1)]
        public struct PyTupleObject
        {
            public uint ob_refcnt;
            public IntPtr ob_type;
            public uint ob_size;
            public IntPtr ob_item;
        }

        [StructLayout(LayoutKind.Sequential, Pack = 1)]
        public struct PySliceObject
        {
            public uint ob_refcnt;
            public IntPtr ob_type;
            public IntPtr start;
            public IntPtr stop;
            public IntPtr step;
        }
        
        [StructLayout(LayoutKind.Sequential, Pack=1)]
        public struct PyListObject
        {
            public uint ob_refcnt;
            public IntPtr ob_type;
            public uint ob_size;
            public IntPtr ob_item;
            public uint allocated;
        }

        [StructLayout(LayoutKind.Sequential, Pack=1)]
        public struct PyStringObject
        {
            public uint ob_refcnt;
            public IntPtr ob_type;
            public uint ob_size;
            public int ob_shash;
            public int ob_sstate;
            public byte ob_sval;
        }
        
        [StructLayout(LayoutKind.Sequential, Pack=1)]
        public struct PyCObject
        {
            public uint ob_refcnt;
            public IntPtr ob_type;
            public IntPtr cobject;
            public IntPtr desc;
            public IntPtr destructor;
        }
        
        [StructLayout(LayoutKind.Sequential, Pack=1)]
        public struct PyTypeObject
        {
            public uint ob_refcnt;
            public IntPtr ob_type;
            public uint ob_size;
            public IntPtr tp_name;
        
            public uint tp_basicsize;
            public uint tp_itemsize;
            public IntPtr tp_dealloc;
            public IntPtr tp_print;

            public IntPtr tp_getattr;
            public IntPtr tp_setattr;
            public IntPtr tp_compare;
            public IntPtr tp_repr;
            
            public IntPtr tp_as_number;
            public IntPtr tp_as_sequence;
            public IntPtr tp_as_mapping;
            public IntPtr tp_hash;

            public IntPtr tp_call;
            public IntPtr tp_str;
            public IntPtr tp_getattro;
            public IntPtr tp_setattro;
            
            public IntPtr tp_as_buffer;
            public uint tp_flags;
            public IntPtr tp_doc;
            public IntPtr tp_traverse;
            
            public IntPtr tp_clear;
            public IntPtr tp_richcompare;
            public IntPtr tp_weaklistoffset;
            public IntPtr tp_iter;

            public IntPtr tp_iternext;
            public IntPtr tp_methods;
            public IntPtr tp_members;
            public IntPtr tp_getset;

            public IntPtr tp_base;
            public IntPtr tp_dict;
            public IntPtr tp_descr_get;
            public IntPtr tp_descr_set;

            public uint tp_dictoffset;
            public IntPtr tp_init;
            public IntPtr tp_alloc;
            public IntPtr tp_new;

            public IntPtr tp_free;
            public IntPtr tp_is_gc;
            public IntPtr tp_bases;
            public IntPtr tp_mro;

            public IntPtr tp_cache;
            public IntPtr tp_subclasses;
            public IntPtr tp_weaklist;
            public IntPtr tp_del;
        }
        
        [StructLayout(LayoutKind.Sequential, Pack=1)]
        public struct PyNumberMethods
        {
            public IntPtr nb_add;
            public IntPtr nb_subtract;
            public IntPtr nb_multiply;
            public IntPtr nb_divide;
            public IntPtr nb_remainder;
            public IntPtr nb_divmod;
            public IntPtr nb_power;
            public IntPtr nb_negative;
            public IntPtr nb_positive;
            public IntPtr nb_absolute;
            public IntPtr nb_nonzero;
            public IntPtr nb_invert;
            public IntPtr nb_lshift;
            public IntPtr nb_rshift;
            public IntPtr nb_and;
            public IntPtr nb_xor;
            public IntPtr nb_or;
            public IntPtr nb_coerce;
            public IntPtr nb_int;
            public IntPtr nb_long;
            public IntPtr nb_float;
            public IntPtr nb_oct;
            public IntPtr nb_hex;
            public IntPtr nb_inplace_add;
            public IntPtr nb_inplace_subtract;
            public IntPtr nb_inplace_multiply;
            public IntPtr nb_inplace_divide;
            public IntPtr nb_inplace_remainder;
            public IntPtr nb_inplace_power;
            public IntPtr nb_inplace_lshift;
            public IntPtr nb_inplace_rshift;
            public IntPtr nb_inplace_and;
            public IntPtr nb_inplace_xor;
            public IntPtr nb_inplace_or;

            /* The following require the Py_TPFLAGS_HAVE_CLASS flag */
            public IntPtr nb_floor_divide;
            public IntPtr nb_true_divide;
            public IntPtr nb_inplace_floor_divide;
            public IntPtr nb_inplace_true_divide;

            public IntPtr nb_index;
        }

        [StructLayout(LayoutKind.Sequential, Pack=1)]
        public struct PySequenceMethods
        {
            public IntPtr sq_length;
            public IntPtr sq_concat;
            public IntPtr sq_repeat;
            public IntPtr sq_item;
            public IntPtr sq_slice;
            public IntPtr sq_ass_item;
            public IntPtr sq_ass_slice;
            public IntPtr sq_contains;
            public IntPtr sq_inplace_concat;
            public IntPtr sq_inplace_repeat;
        }

        [StructLayout(LayoutKind.Sequential, Pack=1)]
        public struct PyMappingMethods
        {
            public IntPtr mp_length;
            public IntPtr mp_subscript;
            public IntPtr mp_ass_subscript;
        }
    }
}

