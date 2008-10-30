
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
    public delegate IntPtr CPython_unaryfunc_Delegate(IntPtr self);

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate IntPtr CPython_binaryfunc_Delegate(IntPtr self, IntPtr arg1);

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate IntPtr CPython_ternaryfunc_Delegate(IntPtr self, IntPtr arg1, IntPtr arg2);


    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate IntPtr CPython_ssizeargfunc_Delegate(IntPtr self, int i);

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate IntPtr CPython_ssizessizeargfunc_Delegate(IntPtr self, int i, int j);

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate int CPython_ssizeobjargproc_Delegate(IntPtr self, int i, IntPtr obj);

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate int CPython_ssizessizeobjargproc_Delegate(IntPtr self, int i, int j, IntPtr obj);

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate int CPython_objobjargproc_Delegate(IntPtr self, IntPtr arg1, IntPtr arg2);
    

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate int CPython_initproc_Delegate(IntPtr self, IntPtr args, IntPtr kwargs);

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate void CPython_destructor_Delegate(IntPtr self);
    

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate IntPtr CPython_getter_Delegate(IntPtr self, IntPtr closure);

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate int CPython_setter_Delegate(IntPtr self, IntPtr value, IntPtr closure);


    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate IntPtr CPython_reprfunc_Delegate(IntPtr self);

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate int CPython_lenfunc_Delegate(IntPtr self);

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate IntPtr CPython_richcmpfunc_Delegate(IntPtr self, IntPtr other, int op);

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate int CPython_inquiry_Delegate(IntPtr self);

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate int CPython_hashfunc_Delegate(IntPtr self);

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate int CPython_cmpfunc_Delegate(IntPtr self, IntPtr other);
}