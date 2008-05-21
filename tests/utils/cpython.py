
from System import IntPtr
from System.Runtime.InteropServices import Marshal
from Ironclad import (
    CPyMarshal, CPython_destructor_Delegate, CPython_getter_Delegate, CPython_initproc_Delegate, CPython_setter_Delegate,
    CPythonVarargsFunction_Delegate, CPythonVarargsKwargsFunction_Delegate, PythonMapper
)
from Ironclad.Structs import METH, Py_TPFLAGS, PyGetSetDef, PyMethodDef, PyTypeObject

from tests.utils.memory import OffsetPtr

gc_fooler = []
def GC_NotYet(dgt):
    gc_fooler.append(dgt)
    def GC_Soon():
        gc_fooler.remove(dgt)
    return GC_Soon

DELEGATE_TYPES = {
    METH.O: CPythonVarargsFunction_Delegate,
    METH.NOARGS: CPythonVarargsFunction_Delegate,
    METH.VARARGS: CPythonVarargsFunction_Delegate,
    METH.VARARGS | METH.KEYWORDS: CPythonVarargsKwargsFunction_Delegate
}
def MakeMethodDef(name, implementation, flags, doc="doc"):
    dgt = DELEGATE_TYPES[flags](implementation)
    return PyMethodDef(name, Marshal.GetFunctionPointerForDelegate(dgt), flags, doc), GC_NotYet(dgt)


def MakeGetSetDef(name, get, set, doc, closure=IntPtr.Zero):
    deallocs = []
    _get = IntPtr.Zero
    if get:
        getdgt = CPython_getter_Delegate(get)
        _get = Marshal.GetFunctionPointerForDelegate(getdgt)
        deallocs.append(GC_NotYet(getdgt))
    _set = IntPtr.Zero
    if set:
        setdgt = CPython_setter_Delegate(set)
        _set = Marshal.GetFunctionPointerForDelegate(setdgt)
        deallocs.append(GC_NotYet(setdgt))
    return PyGetSetDef(name, _get, _set, doc, closure), lambda: map(apply, deallocs)


MAKETYPEPTR_DEFAULTS = {
    "tp_name": "Nemo",
    "tp_doc": "Odysseus' reply to the blinded Cyclops",
    
    "ob_refcnt": 1,
    "tp_basicsize": 8,
    "tp_itemsize": 4,
    "tp_flags": Py_TPFLAGS.HAVE_CLASS,
    
    "tp_methods": None,
    "tp_members": None,
    "tp_getset": None,
    
    "tp_init": lambda _, __, ___: 0,
    "tp_iter": lambda _: IntPtr.Zero,
    "tp_iternext": lambda _: IntPtr.Zero,
}

def GetMapperTypePtrDefaults(mapper):
    return {
        "ob_type": mapper.PyType_Type,
        "tp_alloc": mapper.PyType_GenericAlloc,
        "tp_new": mapper.PyType_GenericNew,
        "tp_dealloc": mapper.PyBaseObject_Dealloc,
        "tp_free": mapper.PyObject_Free,
    }

PTR_ARGS = ("ob_type")
INT_ARGS = ("ob_refcnt", "tp_basicsize", "tp_itemsize", "tp_flags")
STRING_ARGS = ("tp_name", "tp_doc")
TABLE_ARGS = ("tp_methods", "tp_members", "tp_getset")
FUNC_ARGS = {
    "tp_alloc": PythonMapper.PyType_GenericAlloc_Delegate,
    "tp_new": PythonMapper.PyType_GenericNew_Delegate,
    "tp_init": CPython_initproc_Delegate,
    "tp_dealloc": CPython_destructor_Delegate,
    "tp_free": PythonMapper.PyObject_Free_Delegate,
    "tp_iter": PythonMapper.PyObject_GetIter_Delegate,
    "tp_iternext": PythonMapper.PyIter_Next_Delegate,
}

def WriteTypeField(typePtr, name, value):
    if name in PTR_ARGS:
        CPyMarshal.WritePtrField(typePtr, PyTypeObject, name, value)
        return lambda: None
    if name in INT_ARGS:
        CPyMarshal.WriteIntField(typePtr, PyTypeObject, name, int(value))
        return lambda: None
    if name in STRING_ARGS:
        ptr = Marshal.StringToHGlobalAnsi(value)
        CPyMarshal.WritePtrField(typePtr, PyTypeObject, name, ptr)
        return lambda: Marshal.FreeHGlobal(ptr)
    if name in TABLE_ARGS:
        ptr, dealloc = MakeItemsTablePtr(value)
        CPyMarshal.WritePtrField(typePtr, PyTypeObject, name, ptr)
        return dealloc
    if name in FUNC_ARGS:
        dgt = FUNC_ARGS[name](value)
        CPyMarshal.WriteFunctionPtrField(typePtr, PyTypeObject, name, dgt)
        return GC_NotYet(dgt)
    raise KeyError("WriteTypeField can't handle %s, %s" % (name, value))


def MakeTypePtr(mapper, params):
    fields = dict(MAKETYPEPTR_DEFAULTS)
    fields.update(GetMapperTypePtrDefaults(mapper))
    fields.update(params)
    
    typeSize = Marshal.SizeOf(PyTypeObject)
    typePtr = Marshal.AllocHGlobal(typeSize)
    CPyMarshal.Zero(typePtr, typeSize)
    
    deallocs = [lambda: Marshal.FreeHGlobal(typePtr)]
    for field, value in fields.items():
        deallocs.append(WriteTypeField(typePtr, field, value))

    def dealloc():
        for f in deallocs:
            f()
    return typePtr, dealloc


def MakeItemsTablePtr(items):
    if not items:
        return IntPtr.Zero, lambda: None
    itemtype = items[0].__class__
    typesize = Marshal.SizeOf(itemtype)
    size = typesize * (len(items) + 1)
    
    tablePtr = Marshal.AllocHGlobal(size)
    CPyMarshal.Zero(tablePtr, size)
    for i, item in enumerate(items):
        Marshal.StructureToPtr(item, OffsetPtr(tablePtr, typesize * i), False)

    def dealloc():
        Marshal.DestroyStructure(tablePtr, itemtype)
        Marshal.FreeHGlobal(tablePtr)

    return tablePtr, dealloc

