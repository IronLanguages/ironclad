
from tests.utils.runtest import makesuite, run

from tests.utils.memory import OffsetPtr
from tests.utils.testcase import TestCase

from System import IntPtr, Int64, UInt32, UInt64
from System.Runtime.InteropServices import Marshal
from Ironclad import CPyMarshal, Python25Api
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

WritePyTypeObject =  GetWriteBytes(Marshal.SizeOf(PyTypeObject))
TestWrotePyTypeObject = GetTestWroteBytes(Marshal.SizeOf(PyTypeObject))

WritePyObject = GetWriteBytes(Marshal.SizeOf(PyObject))
TestWrotePyObject = GetTestWroteBytes(Marshal.SizeOf(PyObject))

TYPES = (
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
    "_PyWeakref_CallableProxyType",
)

class Python25ApiTest(TestCase):

    def testDataSetterDoesNotWriteForUnrecognisedSymbols(self):
        pm = Python25Api()
        pm.SetData("This_symbol_is_not_exported_either_I_sincerely_hope", IntPtr.Zero)
        # had we written to IntPtr.Zero, we would have crashed


    def assertDataSetterSetsAndRemembers(self, mapperSubclass, dataSymbol, allocSize, memoryTest):
        dataPtr = Marshal.AllocHGlobal(allocSize)
        
        mapper = mapperSubclass()
        mapper.SetData(dataSymbol, dataPtr)
        memoryTest(dataPtr)
        self.assertEquals(getattr(mapper, dataSymbol), dataPtr, "failed to remember pointer")
        
        Marshal.FreeHGlobal(dataPtr)


    def testFinds_Py_NoneStruct(self):
        class MyPM(Python25Api):
            def Fill__Py_NoneStruct(self, address):
                WritePyObject(address)
        self.assertDataSetterSetsAndRemembers(MyPM, "_Py_NoneStruct", Marshal.SizeOf(PyObject), TestWrotePyObject)


    def testFinds_Py_NotImplementedStruct(self):
        class MyPM(Python25Api):
            def Fill__Py_NotImplementedStruct(self, address):
                WritePyObject(address)
        self.assertDataSetterSetsAndRemembers(MyPM, "_Py_NotImplementedStruct", Marshal.SizeOf(PyObject), TestWrotePyObject)
        

    def assertFindsType(self, name):
        class MyPM(Python25Api):
            def fillmethod(self, address):
                WritePyTypeObject(address)
        setattr(MyPM, "Fill_" + name, getattr(MyPM, "fillmethod"))
        self.assertDataSetterSetsAndRemembers(MyPM, name, Marshal.SizeOf(PyTypeObject), TestWrotePyTypeObject)


    def testFindsTypes(self):
        for _type in TYPES:
            self.assertFindsType(_type)
        

    def testUninitialisedTypesAreNull(self):
        pm = Python25Api()
        for _type in TYPES:
            self.assertEquals(getattr(pm, _type), IntPtr.Zero, "unexpected")


    def testAddressGetterFailsCleanly(self):
        pm = Python25Api()
        addressGetter = pm.GetAddress

        self.assertEquals(addressGetter("This_symbol_is_not_exported_by_any_version_of_Python_so_far_as_I_know"),
                          IntPtr.Zero,
                          "bad result for nonsense symbol")


    def assertAddressGetterRemembers(self, mapperSubclass, name, expectedAddress):
        pm = mapperSubclass()

        ptr = pm.GetAddress(name)
        self.assertEquals(ptr, expectedAddress, "unexpected result")
        self.assertEquals(getattr(pm, name), ptr, "did not remember")


    def testPython25ApiFinds_PyExc_SystemError(self):
        class MyPM(Python25Api):
            def Make_PyExc_SystemError(self):
                return IntPtr(999)
        self.assertAddressGetterRemembers(MyPM, "PyExc_SystemError", IntPtr(999))


    def testPython25ApiFinds_PyExc_OverflowError(self):
        class MyPM(Python25Api):
            def Make_PyExc_OverflowError(self):
                return IntPtr(999)
        self.assertAddressGetterRemembers(MyPM, "PyExc_OverflowError", IntPtr(999))




suite = makesuite(
    Python25ApiTest,
)

if __name__ == '__main__':
    run(suite)
