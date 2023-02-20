
from tests.utils.runtest import makesuite, run

from tests.utils.memory import OffsetPtr
from tests.utils.testcase import TestCase

from System import IntPtr, Int64, UInt32, UInt64
from System.Runtime.InteropServices import Marshal
from Ironclad import CPyMarshal, PythonApi
from Ironclad.Structs import Py_complex, PyObject, PyTypeObject

TEST_NUMBER = 1359

def GetTestWroteBytes(bytes):
    intCount = bytes / CPyMarshal.IntSize
    def TestWroteBytes(address):
        for a in range(intCount):
            ptr = OffsetPtr(address, a * CPyMarshal.IntSize)
            data = Marshal.ReadInt32(ptr)
            if data != TEST_NUMBER:
                raise AssertionError("write failed")
    return TestWroteBytes

def GetWriteBytes(bytes):
    intCount = bytes / CPyMarshal.IntSize
    def WriteBytes(address):
        for a in range(intCount):
            ptr = OffsetPtr(address, a * CPyMarshal.IntSize)
            Marshal.WriteInt32(ptr, TEST_NUMBER)
    return WriteBytes

WritePyTypeObject =  GetWriteBytes(Marshal.SizeOf(PyTypeObject()))
TestWrotePyTypeObject = GetTestWroteBytes(Marshal.SizeOf(PyTypeObject()))

WritePyObject = GetWriteBytes(Marshal.SizeOf(PyObject()))
TestWrotePyObject = GetTestWroteBytes(Marshal.SizeOf(PyObject()))

WritePtr = GetWriteBytes(Marshal.SizeOf(IntPtr()))
TestWrotePtr = GetTestWroteBytes(Marshal.SizeOf(IntPtr()))

TYPES = (
    "PyBool_Type",
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
    "PySeqIter_Type",
    "PyCallIter_Type",
    "PyList_Type",
    "PyLong_Type",
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
    "PyTuple_Type",
    "PyUnicode_Type",
    "_PyWeakref_RefType",
    "_PyWeakref_ProxyType",
    "_PyWeakref_CallableProxyType",
)

class PythonApiTest(TestCase):

    def testDataSetterDoesNotWriteForUnrecognisedSymbols(self):
        PythonApi().RegisterData("This_symbol_is_not_exported_either_I_sincerely_hope", IntPtr.Zero)
        # had we written to IntPtr.Zero, we would have crashed


    def assertDataSetterSetsAndRemembers(self, mapperSubclass, dataSymbol, allocSize, memoryTest):
        dataPtr = Marshal.AllocHGlobal(allocSize)
        
        mapper = mapperSubclass()
        mapper.RegisterData(dataSymbol, dataPtr)
        memoryTest(dataPtr)
        self.assertEqual(getattr(mapper, dataSymbol), dataPtr, "failed to remember pointer")
        
        Marshal.FreeHGlobal(dataPtr)


    def testFinds_Py_NoneStruct(self):
        class MyPM(PythonApi):
            def Register__Py_NoneStruct(self, address):
                WritePyObject(address)
        self.assertDataSetterSetsAndRemembers(MyPM, "_Py_NoneStruct", Marshal.SizeOf(PyObject()), TestWrotePyObject)


    def testFinds_Py_NotImplementedStruct(self):
        class MyPM(PythonApi):
            def Register__Py_NotImplementedStruct(self, address):
                WritePyObject(address)
        self.assertDataSetterSetsAndRemembers(MyPM, "_Py_NotImplementedStruct", Marshal.SizeOf(PyObject()), TestWrotePyObject)


    def testFinds_PyExc_OverflowError(self):
        # and, by assertion, all other error types
        # TODO: improve ;)
        class MyPM(PythonApi):
            def Register_PyExc_OverflowError(self, address):
                WritePtr(address)
        self.assertDataSetterSetsAndRemembers(MyPM, "PyExc_OverflowError", Marshal.SizeOf(PyObject()), TestWrotePtr)
        

    def assertFindsType(self, name):
        class MyPM(PythonApi):
            def fillmethod(self, address):
                WritePyTypeObject(address)
        setattr(MyPM, "Register_" + name, getattr(MyPM, "fillmethod"))
        self.assertDataSetterSetsAndRemembers(MyPM, name, Marshal.SizeOf(PyTypeObject()), TestWrotePyTypeObject)


    def testFindsTypes(self):
        for _type in TYPES:
            self.assertFindsType(_type)
        

    def testUninitialisedTypesAreNull(self):
        pa = PythonApi()
        for _type in TYPES:
            self.assertEqual(getattr(pa, _type), IntPtr.Zero, "unexpected")


    def testAddressGetterFailsCleanly(self):
        self.assertEqual(PythonApi().GetFuncPtr("_nonsenx%vQ#*7&"), IntPtr.Zero)


suite = makesuite(
    PythonApiTest,
)

if __name__ == '__main__':
    run(suite)
