
from System import IntPtr, Type
from System.Runtime.InteropServices import Marshal

from Ironclad import CPyMarshal
from Ironclad.Structs import PyObject, PyLongObject, PyTypeObject

def OffsetPtr(ptr, offset):
    if type(offset) == IntPtr:
        offset = offset.ToInt64()
    return IntPtr(ptr.ToInt64() + offset)

# note: PyCode_Type, PyFrame_Type PyTraceBack_Type and PyCFunction_Type
# are not included, because they are implemented in pure C.
# This means that, should an extension end up actually using (say) a buffer type
# and passing it up to IronPython, it will be treated like any other type 
# defined in a C extension.
_types = (
    "PyType_Type",
    "PyBaseObject_Type",
    "PyCell_Type",
    "PyMethod_Type",
    "PyComplex_Type",
    "PyWrapperDescr_Type",
    "PyProperty_Type",
    "PyDict_Type",
    "PyEllipsis_Type",
    "PyEnum_Type",
    "PyReversed_Type",
    "PyFloat_Type",
    "PyFunction_Type",
    "PyClassMethod_Type",
    "PyStaticMethod_Type",
    "PyGen_Type",
    "PyLong_Type",
    "PyBool_Type", # needs to come after PyLong_Type, if it's to have tp_base filled in correctly
    "PySeqIter_Type",
    "PyCallIter_Type",
    "PyList_Type",
    "PyCFunction_Type",
    "PyModule_Type",
    "PySuper_Type",
    "PyRange_Type",
    "PySet_Type",
    "PyFrozenSet_Type",
    "PySlice_Type",
    "PySTEntry_Type",
    "PyBytes_Type",
    "PyTuple_Type",
    "PyUnicode_Type",
    "_PyNone_Type",
    "_PyNotImplemented_Type",
    "_PyWeakref_RefType",
    "_PyWeakref_ProxyType",
    "_PyWeakref_CallableProxyType"
)

sizeOfType = Marshal.SizeOf.Overloads[Type]
PtrToStructure = Marshal.PtrToStructure.Overloads[IntPtr, Type]

_others = {
    "_Py_NoneStruct": sizeOfType(PyObject),
    "_Py_NotImplementedStruct": sizeOfType(PyObject),
    "_Py_EllipsisObject": sizeOfType(PyObject),
    "_Py_FalseStruct": sizeOfType(PyLongObject),
    "_Py_TrueStruct": sizeOfType(PyLongObject),
    "_PyThreadState_Current": sizeOfType(IntPtr),
}
def CreateTypes(mapper, readyTypes=True):
    blocks = []

    def create(name, size):
        block = Marshal.AllocHGlobal(size)
        mapper.RegisterData(name, block)
        blocks.append(block)
    
    for _type in _types:
        create(_type, Marshal.SizeOf(PyTypeObject()))
    for (_other, size) in _others.items():
        create(_other, size)
        
    if readyTypes:
        mapper.ReadyBuiltinTypes()
    
    def DestroyTypes():
        for block in blocks:
            Marshal.FreeHGlobal(block)
    
    return DestroyTypes


