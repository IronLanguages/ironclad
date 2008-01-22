using System;
using System.Runtime.InteropServices;

namespace JumPy
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

    [StructLayout(LayoutKind.Sequential)]
    public struct PyMethodDef
    {
        public string ml_name;
        public IntPtr ml_meth;
        public METH ml_flags;
        public string ml_doc;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct PyObjectHead
    {
        // fixme -- for now, ob_refcnt should not be allowed to reach 0, otherwise we have to implement type objects
        public UInt32 ob_refcnt;
        public IntPtr ob_type;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct PyInt
    {
        public UInt32 ob_refcnt;
        public IntPtr ob_type;
        public Int32 ob_ival;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct PyVarObjectHead
    {
        public UInt32 ob_refcnt;
        public IntPtr ob_type;
        public UInt32 ob_size;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct PyStringHead
    {
        public UInt32 ob_refcnt;
        public IntPtr ob_type;
        public UInt32 ob_size;
        public Int32 ob_shash;
        public UInt32 ob_sstate;
        public IntPtr ob_sval;
    }
}
