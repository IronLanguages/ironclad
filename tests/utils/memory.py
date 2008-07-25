
from System import IntPtr
from System.Runtime.InteropServices import Marshal

from Ironclad.Structs import PyTypeObject

def OffsetPtr(ptr, offset):
    if type(offset) == IntPtr:
        offset = offset.ToInt32()
    return IntPtr(ptr.ToInt32() + offset)

_types = (
    "PyBool_Type",
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
    "_PyWeakref_RefType",
    "_PyWeakref_ProxyType",
    "_PyWeakref_CallableProxyType"
)
def CreateTypes(mapper, readyTypes=True):
    blocks = []
    for _type in _types:
        block = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        mapper.SetData(_type, block)
        blocks.append(block)
    
    if readyTypes:
        mapper.ReadyBuiltinTypes()
    
    def DestroyTypes():
        for block in blocks:
            Marshal.FreeHGlobal(block)
    
    return DestroyTypes