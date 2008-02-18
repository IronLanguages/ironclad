
using System;
using System.Runtime.InteropServices;


namespace JumPy
{
    public delegate IntPtr CPythonVarargsFunction_Delegate(IntPtr self, IntPtr args);

    public delegate IntPtr CPythonVarargsKwargsFunction_Delegate(IntPtr self, IntPtr args, IntPtr kwargs);

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
        public struct PyObject
        {
            public uint ob_refcnt;
            public IntPtr ob_type;
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

