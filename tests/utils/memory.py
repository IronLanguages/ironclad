
from System import IntPtr
from System.Runtime.InteropServices import Marshal

from Ironclad import CPyMarshal
from Ironclad.Structs import PyIntObject, PyObject, PyTypeObject

def OffsetPtr(ptr, offset):
    if type(offset) == IntPtr:
        offset = offset.ToInt32()
    return IntPtr(ptr.ToInt32() + offset)

# note: PyBuffer_Type, PyCObject_Type, PyCode_Type, PyFrame_Type PyTraceBack_Type and PyCFunction_Type
# are not included, because they are implemented in pure C.
# This means that, should an extension end up actually using (say) a buffer type
# and passing it up to IronPython, it will be treated like any other type 
# defined in a C extension.
# PyFile_Type is a special case: it *should* be filled in by C code but, in a test
# context, is usually not. So, we zero it and fill in the one critical method.
_types = (
    "PyType_Type",
    "PyBaseObject_Type",
    "PyCell_Type",
    "PyClass_Type",
    "PyInstance_Type",
    "PyMethod_Type",
    "PyComplex_Type",
    "PyWrapperDescr_Type",
    "PyProperty_Type",
    "PyDict_Type",
    "PyEnum_Type",
    "PyReversed_Type",
    "PyFile_Type",
    "PyFloat_Type",
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
    "PySuper_Type",
    "PyRange_Type",
    "PySet_Type",
    "PyFrozenSet_Type",
    "PySlice_Type",
    "PyBaseString_Type",
    "PySTEntry_Type",
    "PyString_Type",
    "PySymtableEntry_Type",
    "PyTuple_Type",
    "PyUnicode_Type",
    "PyNone_Type", # not exported, for some reason
    "PyEllipsis_Type", # not exported, for some reason
    "PyNotImplemented_Type", # not exported, for some reason
    "_PyWeakref_RefType",
    "_PyWeakref_ProxyType",
    "_PyWeakref_CallableProxyType"
)
_others = {
    "_Py_NoneStruct": Marshal.SizeOf(PyObject),
    "_Py_NotImplementedStruct": Marshal.SizeOf(PyObject),
    "_Py_EllipsisObject": Marshal.SizeOf(PyObject),
    "_Py_ZeroStruct": Marshal.SizeOf(PyIntObject),
    "_Py_TrueStruct": Marshal.SizeOf(PyIntObject),
    "_PyThreadState_Current": Marshal.SizeOf(IntPtr),
}
def CreateTypes(mapper, readyTypes=True):
    blocks = []
    def create(name, size):
        block = Marshal.AllocHGlobal(size)
        if name == 'PyFile_Type':
            CPyMarshal.Zero(block, size);
            CPyMarshal.WritePtrField(block, PyTypeObject, 'tp_dealloc', mapper.GetFuncPtr('IC_file_dealloc'))
        mapper.RegisterData(name, block)
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


