
from System import IntPtr
from System.Runtime.InteropServices import Marshal

import Ironclad
from Ironclad import CPyMarshal
from Ironclad.Structs import METH, Py_TPFLAGS, PyGetSetDef, PyMemberDef, PyMethodDef, PyModuleDef, PyTypeObject

from tests.utils.memory import OffsetPtr
        
def _new_struct(type_, fields, *values):
    struct = type_()
    for field, value in zip(fields, values):
        getattr(type_, field).SetValue(struct, value)
    return struct

_meth_fields = 'ml_name ml_meth ml_flags ml_doc'.split()
new_PyMethodDef = lambda *args: _new_struct(PyMethodDef, _meth_fields, *args)

_getset_fields = 'name get set doc closure'.split()
new_PyGetSetDef = lambda *args: _new_struct(PyGetSetDef, _getset_fields, *args)

_member_fields = 'name type offset flags doc'.split()
new_PyMemberDef = lambda *args: _new_struct(PyMemberDef, _member_fields, *args)

_module_fields = 'ob_refcnt m_name m_doc m_size m_methods'.split()
new_PyModuleDef = lambda *args: _new_struct(PyModuleDef, _module_fields, *args)

gc_fooler = []
def GC_NotYet(dgt):
    gc_fooler.append(dgt)
    def GC_Soon():
        gc_fooler.remove(dgt)
    return GC_Soon

DELEGATE_TYPES = {
    METH.O: Ironclad.dgt_ptr_ptrptr,
    METH.NOARGS: Ironclad.dgt_ptr_ptrptr,
    METH.VARARGS: Ironclad.dgt_ptr_ptrptr,
    METH.KEYWORDS: Ironclad.dgt_ptr_ptrptrptr,
    METH.VARARGS | METH.KEYWORDS: Ironclad.dgt_ptr_ptrptrptr,
}
for (k, v) in list(DELEGATE_TYPES.items()):
    DELEGATE_TYPES[k | METH.COEXIST] = v
def MakeMethodDef(name, implementation, flags, doc="doc"):
    dgt = DELEGATE_TYPES[flags](implementation)
    return new_PyMethodDef(name, Marshal.GetFunctionPointerForDelegate(dgt), int(flags), doc), GC_NotYet(dgt)


def MakeGetSetDef(name, get, set, doc, closure=IntPtr.Zero):
    deallocs = []
    _get = IntPtr.Zero
    if get:
        getdgt = Ironclad.dgt_ptr_ptrptr(get)
        _get = Marshal.GetFunctionPointerForDelegate(getdgt)
        deallocs.append(GC_NotYet(getdgt))
    _set = IntPtr.Zero
    if set:
        setdgt = Ironclad.dgt_int_ptrptrptr(set)
        _set = Marshal.GetFunctionPointerForDelegate(setdgt)
        deallocs.append(GC_NotYet(setdgt))
    return new_PyGetSetDef(name, _get, _set, doc, closure), lambda: [f() for f in deallocs]


def MakeMemberDef(name, type_, offset, flags, doc="doc"):
    return new_PyMemberDef(name, int(type_), offset, flags, doc), lambda: None


def MakeModuleDef(name, methods, doc):
    moduleDef = new_PyModuleDef(1, name, doc, -1, methods)
    ptr = Marshal.AllocHGlobal(Marshal.SizeOf(moduleDef))
    Marshal.StructureToPtr(moduleDef, ptr, False)

    # TODO: maybe we shouldn't dealloc, the module is supposed to keep a reference to the module def...
    def dealloc():
        Marshal.DestroyStructure(ptr, PyModuleDef)
        Marshal.FreeHGlobal(ptr)

    return ptr, dealloc


MAKETYPEPTR_DEFAULTS = {
    "tp_name": "Nemo",
    "tp_doc": "Odysseus' reply to the blinded Cyclops",
    
    "ob_refcnt": 1,
    "tp_basicsize": 2 * IntPtr.Size,
    "tp_itemsize": IntPtr.Size,
    "tp_flags": 0,
    
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
        "tp_dealloc": mapper.IC_PyBaseObject_Dealloc,
        "tp_free": mapper.PyObject_Free,
    }

PTR_ARGS = ("ob_refcnt", "ob_type", "tp_basicsize", "tp_itemsize", "tp_base", "tp_bases", "tp_as_number", "tp_as_sequence", "tp_as_mapping")
INT_ARGS = ("tp_flags")
STRING_ARGS = ("tp_name", "tp_doc")
TABLE_ARGS = ("tp_methods", "tp_members", "tp_getset")
FUNC_ARGS = {
    "tp_alloc": Ironclad.dgt_ptr_ptrssize,
    "tp_new": Ironclad.dgt_ptr_ptrptrptr,
    "tp_init": Ironclad.dgt_int_ptrptrptr,
    "tp_dealloc": Ironclad.dgt_void_ptr,
    "tp_free": Ironclad.dgt_void_ptr,
    "tp_getattr": Ironclad.dgt_ptr_ptrstr,
    "tp_iter": Ironclad.dgt_ptr_ptr,
    "tp_iternext": Ironclad.dgt_ptr_ptr,
    "tp_call": Ironclad.dgt_ptr_ptrptrptr,
    "tp_str": Ironclad.dgt_ptr_ptr,
    "tp_repr": Ironclad.dgt_ptr_ptr,
    "tp_richcompare": Ironclad.dgt_ptr_ptrptrint,
    "tp_hash": Ironclad.dgt_ssize_ptr,
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
    typeSize = IntPtr(Marshal.SizeOf(PyTypeObject()))
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
    typesize = Marshal.SizeOf(itemtype())
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
    "nb_negative": Ironclad.dgt_ptr_ptr, 
    "nb_positive": Ironclad.dgt_ptr_ptr, 
    "nb_absolute": Ironclad.dgt_ptr_ptr, 
    "nb_invert": Ironclad.dgt_ptr_ptr, 
    "nb_int": Ironclad.dgt_ptr_ptr, 
    "nb_float": Ironclad.dgt_ptr_ptr, 
    "nb_index": Ironclad.dgt_ptr_ptr, 
    
    "nb_add": Ironclad.dgt_ptr_ptrptr, 
    "nb_subtract": Ironclad.dgt_ptr_ptrptr, 
    "nb_multiply": Ironclad.dgt_ptr_ptrptr, 
    "nb_floor_divide": Ironclad.dgt_ptr_ptrptr, 
    "nb_true_divide": Ironclad.dgt_ptr_ptrptr, 
    "nb_remainder": Ironclad.dgt_ptr_ptrptr, 
    "nb_divmod": Ironclad.dgt_ptr_ptrptr, 
    "nb_lshift": Ironclad.dgt_ptr_ptrptr, 
    "nb_rshift": Ironclad.dgt_ptr_ptrptr, 
    "nb_and": Ironclad.dgt_ptr_ptrptr, 
    "nb_xor": Ironclad.dgt_ptr_ptrptr, 
    "nb_or": Ironclad.dgt_ptr_ptrptr, 
    
    "nb_inplace_add": Ironclad.dgt_ptr_ptrptr, 
    "nb_inplace_subtract": Ironclad.dgt_ptr_ptrptr, 
    "nb_inplace_multiply": Ironclad.dgt_ptr_ptrptr, 
    "nb_inplace_floor_divide": Ironclad.dgt_ptr_ptrptr, 
    "nb_inplace_true_divide": Ironclad.dgt_ptr_ptrptr, 
    "nb_inplace_remainder": Ironclad.dgt_ptr_ptrptr, 
    "nb_inplace_lshift": Ironclad.dgt_ptr_ptrptr, 
    "nb_inplace_rshift": Ironclad.dgt_ptr_ptrptr, 
    "nb_inplace_and": Ironclad.dgt_ptr_ptrptr, 
    "nb_inplace_xor": Ironclad.dgt_ptr_ptrptr, 
    "nb_inplace_or": Ironclad.dgt_ptr_ptrptr, 
    
    "nb_bool": Ironclad.dgt_int_ptr,
    "nb_power": Ironclad.dgt_ptr_ptrptrptr, 
    "nb_inplace_power": Ironclad.dgt_ptr_ptrptrptr, 
    
    "sq_item": Ironclad.dgt_ptr_ptrssize,
    "sq_concat": Ironclad.dgt_ptr_ptrptr,
    "sq_repeat": Ironclad.dgt_ptr_ptrssize,
    "sq_ass_item": Ironclad.dgt_int_ptrssizeptr,
    "sq_length": Ironclad.dgt_ssize_ptr,
    "sq_contains": Ironclad.dgt_int_ptrptr,
    
    "mp_length": Ironclad.dgt_ssize_ptr,
    "mp_subscript": Ironclad.dgt_ptr_ptrptr,
    "mp_ass_subscript": Ironclad.dgt_int_ptrptrptr,
}

def MakeNumSeqMapMethods(_type, slots):
    size = Marshal.SizeOf(_type())
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
