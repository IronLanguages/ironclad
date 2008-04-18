
from System import IntPtr
from System.Runtime.InteropServices import Marshal
from Ironclad import (
    CPyMarshal, CPython_initproc_Delegate, CPythonVarargsFunction_Delegate,
    CPythonVarargsKwargsFunction_Delegate, PythonMapper
)
from Ironclad.Structs import METH, Py_TPFLAGS, PyMethodDef, PyTypeObject

from tests.utils.memory import OffsetPtr


gc_fooler = []
def MakeMethodDef(name, implementation, flags, doc="doc"):
    if flags in (METH.VARARGS, METH.NOARGS, METH.O):
        dgt = CPythonVarargsFunction_Delegate(implementation)
    elif flags == METH.VARARGS | METH.KEYWORDS:
        dgt = CPythonVarargsKwargsFunction_Delegate(implementation)
    gc_fooler.append(dgt)
    return PyMethodDef(name, Marshal.GetFunctionPointerForDelegate(dgt), flags, doc)



Null_tp_init_Func = lambda _, __, ___: 0
Null_tp_init_Delegate = CPython_initproc_Delegate(Null_tp_init_Func)
Null_tp_init_FP = Marshal.GetFunctionPointerForDelegate(Null_tp_init_Delegate)

Null_tp_new_Func = lambda _, __, ___: IntPtr(12345)
Null_tp_new_Delegate = PythonMapper.PyType_GenericNew_Delegate(Null_tp_new_Func)
Null_tp_new_FP = Marshal.GetFunctionPointerForDelegate(Null_tp_new_Delegate)

def MakeTypePtr(tp_name, typeTypePtr,
                basicSize=8, itemSize=4, methodDef=None, tp_flags=Py_TPFLAGS.HAVE_CLASS,
                tp_doc="",
                tp_allocPtr=IntPtr.Zero, tp_newPtr=Null_tp_new_FP, tp_initPtr=Null_tp_init_FP, 
                tp_iterPtr=IntPtr.Zero, tp_iternextPtr=IntPtr.Zero):
    typePtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
    namePtr = Marshal.StringToHGlobalAnsi(tp_name)
    docPtr = Marshal.StringToHGlobalAnsi(tp_doc)
    methodsPtr, deallocMethods = MakeSingleMethodTablePtr(methodDef)

    def WriteField(fieldName, writerName, value):
        offset = Marshal.OffsetOf(PyTypeObject, fieldName)
        address = OffsetPtr(typePtr, offset)
        getattr(CPyMarshal, writerName)(address, value)

    WriteField("ob_refcnt", "WriteInt", 1)
    WriteField("ob_type", "WritePtr", typeTypePtr)

    WriteField("tp_basicsize", "WriteInt", basicSize)
    WriteField("tp_itemsize", "WriteInt", itemSize)
    
    WriteField("tp_flags", "WriteInt", int(tp_flags))

    WriteField("tp_name", "WritePtr", namePtr)
    WriteField("tp_doc", "WritePtr", docPtr)
    WriteField("tp_methods", "WritePtr", methodsPtr)
    WriteField("tp_alloc", "WritePtr", tp_allocPtr)
    WriteField("tp_new", "WritePtr", tp_newPtr)
    WriteField("tp_init", "WritePtr", tp_initPtr)
    WriteField("tp_iter", "WritePtr", tp_iterPtr)
    WriteField("tp_iternext", "WritePtr", tp_iternextPtr)

    def dealloc():
        Marshal.FreeHGlobal(typePtr)
        Marshal.FreeHGlobal(namePtr)
        Marshal.FreeHGlobal(docPtr)
        deallocMethods()

    return typePtr, dealloc


def MakeSingleMethodTablePtr(methodDef):
    if methodDef is None:
        return IntPtr.Zero, lambda: None
    size = Marshal.SizeOf(PyMethodDef)
    methodsPtr = Marshal.AllocHGlobal(size * 2)
    Marshal.StructureToPtr(methodDef, methodsPtr, False)
    terminator = OffsetPtr(methodsPtr, size)
    CPyMarshal.WriteInt(terminator, 0)

    def dealloc():
        Marshal.DestroyStructure(methodsPtr, PyMethodDef)
        Marshal.FreeHGlobal(methodsPtr)

    return methodsPtr, dealloc

