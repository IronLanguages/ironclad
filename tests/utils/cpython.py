
from System import IntPtr
from System.Runtime.InteropServices import Marshal
from Ironclad import (
    CPyMarshal, Python25Api, 
    CPython_initproc_Delegate, CPython_destructor_Delegate, 
    CPython_getter_Delegate, CPython_setter_Delegate,
    CPython_unaryfunc_Delegate, CPython_binaryfunc_Delegate, CPython_ternaryfunc_Delegate, 
    CPython_ssizeargfunc_Delegate, CPython_ssizessizeargfunc_Delegate,
    CPython_ssizeobjargproc_Delegate, CPython_ssizessizeobjargproc_Delegate, CPython_objobjargproc_Delegate,
    CPython_reprfunc_Delegate, CPython_lenfunc_Delegate, CPython_richcmpfunc_Delegate, CPython_inquiry_Delegate,
    CPythonVarargsFunction_Delegate, CPythonVarargsKwargsFunction_Delegate, 
    CPython_cmpfunc_Delegate, CPython_getattr_Delegate, CPython_hashfunc_Delegate
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
    
    "tp_init": None,
    "tp_iter": None,
    "tp_iternext": None,
    
    "tp_base": IntPtr.Zero,
    "tp_bases": IntPtr.Zero,
    "tp_as_number": IntPtr.Zero,
}

def GetMapperTypePtrDefaults(mapper):
    return {
        "ob_type": mapper.PyType_Type,
        "tp_alloc": mapper.PyType_GenericAlloc,
        "tp_new": mapper.PyType_GenericNew,
        "tp_dealloc": mapper.PyBaseObject_Dealloc,
        "tp_free": mapper.PyObject_Free,
    }

PTR_ARGS = ("ob_type", "tp_base", "tp_bases", "tp_as_number", "tp_as_sequence", "tp_as_mapping")
INT_ARGS = ("ob_refcnt", "tp_basicsize", "tp_itemsize", "tp_flags")
STRING_ARGS = ("tp_name", "tp_doc")
TABLE_ARGS = ("tp_methods", "tp_members", "tp_getset")
FUNC_ARGS = {
    "tp_alloc": Python25Api.PyType_GenericAlloc_Delegate,
    "tp_new": Python25Api.PyType_GenericNew_Delegate,
    "tp_init": CPython_initproc_Delegate,
    "tp_dealloc": CPython_destructor_Delegate,
    "tp_free": Python25Api.PyObject_Free_Delegate,
    "tp_getattr": CPython_getattr_Delegate,
    "tp_iter": Python25Api.PyObject_GetIter_Delegate,
    "tp_iternext": Python25Api.PyIter_Next_Delegate,
    "tp_call": CPythonVarargsKwargsFunction_Delegate,
    "tp_str": CPython_reprfunc_Delegate,
    "tp_repr": CPython_reprfunc_Delegate,
    "tp_richcompare": CPython_richcmpfunc_Delegate,
    "tp_compare": CPython_cmpfunc_Delegate,
    "tp_hash": CPython_hashfunc_Delegate,
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
        if value is not None:
            dgt = FUNC_ARGS[name](value)
            CPyMarshal.WriteFunctionPtrField(typePtr, PyTypeObject, name, dgt)
            return GC_NotYet(dgt)
        return lambda: None
    raise KeyError("WriteTypeField can't handle %s, %s" % (name, value))


def MakeTypePtr(mapper, params, allocator=None):
    fields = dict(MAKETYPEPTR_DEFAULTS)
    fields.update(GetMapperTypePtrDefaults(mapper))
    fields.update(params)
    
    deallocs = []
    typeSize = Marshal.SizeOf(PyTypeObject)
    if allocator:
        # pretend this was constructed by a C extension, using the mapper's allocator
        # hence mapper should do the deallocation itself
        typePtr = allocator.Alloc(typeSize)
    else:
        typePtr = Marshal.AllocHGlobal(typeSize)
        deallocs.append(lambda: Marshal.FreeHGlobal(typePtr))
    CPyMarshal.Zero(typePtr, typeSize)
    
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

NUMSEQMAP_METHODS = {
    "nb_negative": CPython_unaryfunc_Delegate, 
    "nb_positive": CPython_unaryfunc_Delegate, 
    "nb_absolute": CPython_unaryfunc_Delegate, 
    "nb_invert": CPython_unaryfunc_Delegate, 
    "nb_int": CPython_unaryfunc_Delegate, 
    "nb_long": CPython_unaryfunc_Delegate, 
    "nb_float": CPython_unaryfunc_Delegate, 
    "nb_oct": CPython_unaryfunc_Delegate, 
    "nb_hex": CPython_unaryfunc_Delegate, 
    "nb_index": CPython_unaryfunc_Delegate, 
    
    "nb_add": CPython_binaryfunc_Delegate, 
    "nb_subtract": CPython_binaryfunc_Delegate, 
    "nb_multiply": CPython_binaryfunc_Delegate, 
    "nb_divide": CPython_binaryfunc_Delegate, 
    "nb_floor_divide": CPython_binaryfunc_Delegate, 
    "nb_true_divide": CPython_binaryfunc_Delegate, 
    "nb_remainder": CPython_binaryfunc_Delegate, 
    "nb_divmod": CPython_binaryfunc_Delegate, 
    "nb_lshift": CPython_binaryfunc_Delegate, 
    "nb_rshift": CPython_binaryfunc_Delegate, 
    "nb_and": CPython_binaryfunc_Delegate, 
    "nb_xor": CPython_binaryfunc_Delegate, 
    "nb_or": CPython_binaryfunc_Delegate, 
    
    "nb_inplace_add": CPython_binaryfunc_Delegate, 
    "nb_inplace_subtract": CPython_binaryfunc_Delegate, 
    "nb_inplace_multiply": CPython_binaryfunc_Delegate, 
    "nb_inplace_divide": CPython_binaryfunc_Delegate, 
    "nb_inplace_floor_divide": CPython_binaryfunc_Delegate, 
    "nb_inplace_true_divide": CPython_binaryfunc_Delegate, 
    "nb_inplace_remainder": CPython_binaryfunc_Delegate, 
    "nb_inplace_lshift": CPython_binaryfunc_Delegate, 
    "nb_inplace_rshift": CPython_binaryfunc_Delegate, 
    "nb_inplace_and": CPython_binaryfunc_Delegate, 
    "nb_inplace_xor": CPython_binaryfunc_Delegate, 
    "nb_inplace_or": CPython_binaryfunc_Delegate, 
    
    "nb_nonzero": CPython_inquiry_Delegate,
    "nb_power": CPython_ternaryfunc_Delegate, 
    "nb_inplace_power": CPython_ternaryfunc_Delegate, 
    
    "sq_item": CPython_ssizeargfunc_Delegate,
    "sq_concat": CPython_binaryfunc_Delegate,
    "sq_repeat": CPython_ssizeargfunc_Delegate,
    "sq_slice": CPython_ssizessizeargfunc_Delegate,
    "sq_ass_item": CPython_ssizeobjargproc_Delegate,
    "sq_ass_slice": CPython_ssizessizeobjargproc_Delegate,
    "sq_length": CPython_lenfunc_Delegate,
    
    "mp_length": CPython_lenfunc_Delegate,
    "mp_subscript": CPython_binaryfunc_Delegate,
    "mp_ass_subscript": CPython_objobjargproc_Delegate,
}

def MakeNumSeqMapMethods(_type, slots):
    size = Marshal.SizeOf(_type)
    ptr = Marshal.AllocHGlobal(size)
    CPyMarshal.Zero(ptr, size)
    deallocs = []
    for (slot, func) in slots.items():
        dgt = NUMSEQMAP_METHODS[slot](func)
        CPyMarshal.WriteFunctionPtrField(ptr, _type, slot, dgt)
        deallocs.append(GC_NotYet(dgt))
        
    def dealloc():
        for f in deallocs:
            f()
        Marshal.FreeHGlobal(ptr)
    return ptr, dealloc
