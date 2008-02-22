
from System import IntPtr
from System.Runtime.InteropServices import Marshal
from Ironclad import (
    CPyMarshal, CPython_initproc_Delegate, CPythonVarargsFunction_Delegate,
    CPythonVarargsKwargsFunction_Delegate
)
from Ironclad.Structs import METH, PyMethodDef, PyTypeObject

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


def MakeTypePtr(tp_name, typeTypePtr,
                basicSize=8, itemSize=4, methodDef=None,
                tp_allocPtr=IntPtr.Zero, tp_newPtr=IntPtr.Zero,
                tp_initPtr=Null_tp_init_FP):
    typePtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
    namePtr = Marshal.StringToHGlobalAnsi(tp_name)
    methodsPtr, deallocMethods = MakeSingleMethodTablePtr(methodDef)

    def WriteField(fieldName, writerName, value):
        offset = Marshal.OffsetOf(PyTypeObject, fieldName)
        address = OffsetPtr(typePtr, offset)
        getattr(CPyMarshal, writerName)(address, value)

    WriteField("ob_refcnt", "WriteInt", 1)
    WriteField("ob_type", "WritePtr", typeTypePtr)

    WriteField("tp_basicsize", "WriteInt", basicSize)
    WriteField("tp_itemsize", "WriteInt", itemSize)

    WriteField("tp_name", "WritePtr", namePtr)
    WriteField("tp_methods", "WritePtr", methodsPtr)
    WriteField("tp_alloc", "WritePtr", tp_allocPtr)
    WriteField("tp_new", "WritePtr", tp_newPtr)
    WriteField("tp_init", "WritePtr", tp_initPtr)

    def dealloc():
        Marshal.FreeHGlobal(typePtr)
        Marshal.FreeHGlobal(namePtr)
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

