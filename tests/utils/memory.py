
from System import IntPtr
from System.Runtime.InteropServices import Marshal

from Ironclad.Structs import PyIntObject, PyObject, PyTypeObject

def OffsetPtr(ptr, offset):
    if type(offset) == IntPtr:
        offset = offset.ToInt32()
    return IntPtr(ptr.ToInt32() + offset)

_types = (
    "PyBuffer_Type",
    "PyCell_Type",
    "PyClass_Type",
    "PyInstance_Type",
    "PyMethod_Type",
    "PyCObject_Type",
    "PyCode_Type",
    "PyComplex_Type",
    "PyWrapperDescr_Type",
    "PyProperty_Type",
    "PyDict_Type",
    "PyEnum_Type",
    "PyReversed_Type",
    "PyFile_Type",
    "PyFloat_Type",
    "PyFrame_Type",
    "PyFunction_Type",
    "PyClassMethod_Type",
    "PyStaticMethod_Type",
    "PyGen_Type",
    "PyInt_Type",
    "PyBool_Type", # needs to come after PyInt_Type, if it's to have tp_base filled in correctly
    "PySeqIter_Type",
    "PyCallIter_Type",
    "PyList_Type",
    "PyLong_Type",
    "PyCFunction_Type",
    "PyModule_Type",
    "PyType_Type",
    "PyBaseObject_Type",
    "PySuper_Type",
    "PyRange_Type",
    "PySet_Type",
    "PyFrozenSet_Type",
    "PySlice_Type",
    "PyBaseString_Type",
    "PySTEntry_Type",
    "PyString_Type",
    "PySymtableEntry_Type",
    "PyTraceBack_Type",
    "PyTuple_Type",
    "PyUnicode_Type",
    "PyNone_Type", # not exported, for some reason
    "PyEllipsis_Type", # not exported, for some reason
    "_PyWeakref_RefType",
    "_PyWeakref_ProxyType",
    "_PyWeakref_CallableProxyType"
)
_others = {
    "_Py_NoneStruct": Marshal.SizeOf(PyObject),
    "_Py_EllipsisObject": Marshal.SizeOf(PyObject),
    "_Py_ZeroStruct": Marshal.SizeOf(PyIntObject),
    "_Py_TrueStruct": Marshal.SizeOf(PyIntObject),
}
def CreateTypes(mapper, readyTypes=True):
    blocks = []
    def create(name, size):
        block = Marshal.AllocHGlobal(size)
        mapper.SetData(name, block)
        blocks.append(block)
    
    for _type in _types:
        create(_type, Marshal.SizeOf(PyTypeObject))
    for (_other, size) in _others.items():
        create(_other, size)
        
    if readyTypes:
        mapper.ReadyBuiltinTypes()
    
    def DestroyTypes():
        for block in blocks:
            Marshal.FreeHGlobal(block)
    
    return DestroyTypes