
using System;
using System.Runtime.InteropServices;


namespace Ironclad
{
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate IntPtr CPythonSelfFunction_Delegate(IntPtr self);

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate IntPtr CPythonVarargsFunction_Delegate(IntPtr self, IntPtr args);

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate IntPtr CPythonVarargsKwargsFunction_Delegate(IntPtr self, IntPtr args, IntPtr kwargs);
    

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate int CPython_initproc_Delegate(IntPtr self, IntPtr args, IntPtr kwargs);

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate void CPython_destructor_Delegate(IntPtr self);
    

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate IntPtr CPython_getter_Delegate(IntPtr self, IntPtr closure);

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate int CPython_setter_Delegate(IntPtr self, IntPtr value, IntPtr closure);


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

            public PyGetSetDef(string name, IntPtr get, IntPtr set, string doc)
            {
                this.name = name;
                this.get = get;
                this.set = set;
                this.doc = doc;
                this.closure = IntPtr.Zero;
            }
        }
        
        [StructLayout(LayoutKind.Sequential, Pack=1)]
        public struct PyObject
        {
            public uint ob_refcnt;
            public IntPtr ob_type;
        }
        
        [StructLayout(LayoutKind.Sequential, Pack=1)]
        public struct PyTupleObject
        {
            public uint ob_refcnt;
            public IntPtr ob_type;
            public uint ob_size;
            public IntPtr ob_item;
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

    }
}

