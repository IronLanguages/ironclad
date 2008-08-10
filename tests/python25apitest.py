
from tests.utils.runtest import makesuite, run

from tests.utils.memory import OffsetPtr
from tests.utils.testcase import TestCase

from System import IntPtr, Int64, UInt32, UInt64
from System.Runtime.InteropServices import Marshal
from Ironclad import CPyMarshal, Python25Api
from Ironclad.Structs import PyObject, PyTypeObject

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
        self.assertDataSetterSetsAndRemembers(MyPM, "_Py_NoneStruct", Marshal.SizeOf(PyTypeObject), TestWrotePyObject)
        

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



FIND_TEST_CODE = """
class MyPM(Python25Api):
    def %(name)s(self, %(argnames)s):
        self.call = (%(argnames)s,)
        return %(retval)s
self.assertDispatches(
    MyPM, "%(name)s", %(args)s, %(retval)s)
"""

FIND_TEST_CODE_NOARGS = """
class MyPM(Python25Api):
    def %(name)s(self):
        self.call = tuple()
        return %(retval)s
self.assertDispatches(
    MyPM, "%(name)s", tuple(), %(retval)s)
"""

class Python25ApiFunctionsTest(TestCase):

    def assertDispatches(self, mapperSubclass, funcName, argTuple, expectedResult):
        pm = mapperSubclass()

        fp1 = pm.GetAddress(funcName)
        self.assertNotEquals(fp1, IntPtr.Zero, "unexpected nullity")
        fp2 = pm.GetAddress(funcName)
        self.assertEquals(fp1, fp2, "2 calls produced different pointers")

        # we need to keep a reference to dgt, in case of inconvenient GCs
        self.dgt = Marshal.GetDelegateForFunctionPointer(fp1, getattr(Python25Api, funcName + "_Delegate"))
        result = self.dgt(*argTuple)

        self.assertEquals(result, expectedResult, "unexpected result")
        self.assertEquals(pm.call, argTuple, "wrong params stored")


    def assertFinds(self, name, args, retval):
        info = dict(
            name = name,
            args = '(%s,)' % ', '.join(args),
            retval = retval,
            argnames = ', '.join([('arg%d' % i) for i in range(len(args))]),
        )
        if args:
            exec(FIND_TEST_CODE % info)
        else:
            exec(FIND_TEST_CODE_NOARGS % info)


    def testPython25ApiFindsMethods(self):
        self.assertFinds("Py_InitModule4", ('"name"', 'IntPtr.Zero', '"doc"', 'IntPtr.Zero', '12345'), 'IntPtr.Zero')
        self.assertFinds("PyModule_AddObject", ('IntPtr(33)', '"henry"', 'IntPtr(943)'), '33')
        self.assertFinds("PyModule_AddIntConstant", ('IntPtr(33)', '"henry"', '123'), '33')
        self.assertFinds("PyModule_AddStringConstant", ('IntPtr(33)', '"henry"', '"clanger"'), '33')
        self.assertFinds("PyModule_GetDict", ('IntPtr(943)',), 'IntPtr(33)')
        
        self.assertFinds("PyImport_ImportModule", ('"name"', ), 'IntPtr(123)')
        self.assertFinds("PyImport_AddModule", ('"name"', ), 'IntPtr(123)')
        self.assertFinds("PyImport_Import", ('IntPtr(111)', ), 'IntPtr(123)')
        
        self.assertFinds("PyErr_SetString", ('IntPtr(98765)', '"and in the darkness bind them"'), 'None')
        self.assertFinds("PyErr_NewException", ('"foo.bar.bazerror"', 'IntPtr(111)', 'IntPtr(222)'), 'IntPtr(999)')
        self.assertFinds("PyErr_Occurred", tuple(), 'IntPtr(123)')
        self.assertFinds("PyErr_Clear", tuple(), 'None')
        self.assertFinds("PyErr_Print", tuple(), 'None')
        
        self.assertFinds("PyType_GenericNew", ('IntPtr(111)', 'IntPtr(222)', 'IntPtr(333)'), 'IntPtr(999)')
        self.assertFinds("PyType_GenericAlloc", ('IntPtr(111)', '22'), 'IntPtr(999)')
        self.assertFinds("PyType_IsSubtype", ('IntPtr(111)', 'IntPtr(222)'), '123')
        self.assertFinds("PyType_Ready", ('IntPtr(111)',), '123')
        
        self.assertFinds("PyObject_Call", ('IntPtr(123)', 'IntPtr(456)', 'IntPtr(789)'), 'IntPtr(999)')
        self.assertFinds("PyObject_GetIter", ('IntPtr(123)',), 'IntPtr(999)')
        self.assertFinds("PyObject_HasAttrString", ('IntPtr(111)', '"harold"'), '999')
        self.assertFinds("PyObject_GetAttrString", ('IntPtr(111)', '"harold"'), 'IntPtr(999)')
        self.assertFinds("PyObject_GetAttr", ('IntPtr(111)', 'IntPtr(222)'), 'IntPtr(999)')
        self.assertFinds("PyObject_SetAttrString", ('IntPtr(111)', '"harold"', 'IntPtr(222)'), '123')
        self.assertFinds("PyObject_SetAttr", ('IntPtr(111)', 'IntPtr(222)', 'IntPtr(333)'), '123')
        self.assertFinds("PyObject_Free", ('IntPtr(111)',), 'None')
        self.assertFinds("PyObject_Init", ('IntPtr(111)', 'IntPtr(222)'), 'IntPtr(999)')
        self.assertFinds("PyObject_IsTrue", ('IntPtr(111)',), '123')
        self.assertFinds("PyObject_Size", ('IntPtr(111)',), '123')
        self.assertFinds("PyObject_Str", ('IntPtr(111)',), 'IntPtr(999)')
        self.assertFinds("_PyObject_New", ('IntPtr(111)',), 'IntPtr(999)')
        
        self.assertFinds("PyCallable_Check", ('IntPtr(111)',), '0')
        
        self.assertFinds("PySequence_Check", ('IntPtr(111)',), '0')
        self.assertFinds("PySequence_Size", ('IntPtr(111)',), '123')
        self.assertFinds("PySequence_GetItem", ('IntPtr(111)', '123'), 'IntPtr(999)')
        
        self.assertFinds("PyIter_Next", ('IntPtr(123)',), 'IntPtr(999)')
        
        self.assertFinds("PyDict_New", tuple(), 'IntPtr(999)')
        self.assertFinds("PyDict_Size", ('IntPtr(111)',), '999')
        self.assertFinds("PyDict_GetItem", ('IntPtr(111)', 'IntPtr(222)'), 'IntPtr(333)')
        self.assertFinds("PyDict_GetItemString", ('IntPtr(111)', '"boojum"'), 'IntPtr(999)')
        self.assertFinds("PyDict_SetItem", ('IntPtr(111)', 'IntPtr(222)', 'IntPtr(333)'), '123')
        self.assertFinds("PyDict_SetItemString", ('IntPtr(111)', '"boojum"', 'IntPtr(999)'), '123')
        
        self.assertFinds("PyList_New", ('33',), 'IntPtr(999)')
        self.assertFinds("PyList_Append", ('IntPtr(123)', 'IntPtr(456)'), '789')
        self.assertFinds("PyList_SetItem", ('IntPtr(123)', '4', 'IntPtr(567)'), '999')
        self.assertFinds("PyList_GetSlice", ('IntPtr(123)', '4', '5'), 'IntPtr(789)')
        
        self.assertFinds("PyTuple_New", ('33',), 'IntPtr(999)')
        self.assertFinds("PyTuple_Size", ('IntPtr(111)',), '999')
        
        self.assertFinds("PyNumber_Add", ('IntPtr(111)', 'IntPtr(222)'), 'IntPtr(999)')
        self.assertFinds("PyNumber_Subtract", ('IntPtr(111)', 'IntPtr(222)'), 'IntPtr(999)')
        self.assertFinds("PyNumber_Multiply", ('IntPtr(111)', 'IntPtr(222)'), 'IntPtr(999)')
        self.assertFinds("PyNumber_Divide", ('IntPtr(111)', 'IntPtr(222)'), 'IntPtr(999)')
        self.assertFinds("PyNumber_Absolute", ('IntPtr(111)',), 'IntPtr(999)')
        self.assertFinds("PyNumber_Long", ('IntPtr(111)',), 'IntPtr(999)')
        self.assertFinds("PyNumber_Float", ('IntPtr(111)',), 'IntPtr(999)')
        
        self.assertFinds("PyString_AsString", ('IntPtr(98765)',), 'IntPtr(12345)')
        self.assertFinds("PyString_FromString", ('IntPtr(333)',), 'IntPtr(444)')
        self.assertFinds("PyString_FromStringAndSize", ('IntPtr(98765)', '33'), 'IntPtr(12345)')
        self.assertFinds("PyString_Size", ('IntPtr(98765)',), '123')
        self.assertFinds("_PyString_Resize", ('IntPtr(98765)', '33'), '0')
        self.assertFinds("PyString_InternFromString", ('IntPtr(333)',), 'IntPtr(444)')
        self.assertFinds("PyString_InternInPlace", ('IntPtr(333)',), 'None')
        
        self.assertFinds("PyInt_FromLong", ('33',), 'IntPtr(999)')
        self.assertFinds("PyInt_FromSsize_t", ('33',), 'IntPtr(999)')
        self.assertFinds("PyInt_AsLong", ('IntPtr(123)',), '999')
        
        self.assertFinds("PyLong_AsLong", ('IntPtr(999)',), '2000000000')
        self.assertFinds("PyLong_AsLongLong", ('IntPtr(999)',), 'Int64(5555555555)')
        self.assertFinds("PyLong_FromLongLong", ('Int64(5555555555)',), 'IntPtr(999)')
        self.assertFinds("PyLong_FromUnsignedLong", ('UInt32(4000000000)',), 'IntPtr(999)')
        self.assertFinds("PyLong_FromUnsignedLongLong", ('UInt64(18000000000000000000)',), 'IntPtr(999)')
        
        self.assertFinds("PyFloat_FromDouble", ('33.3',), 'IntPtr(999)')
        self.assertFinds("PyFloat_AsDouble", ('IntPtr(111)',), '123.45')
        
        self.assertFinds("PyFile_AsFile", ('IntPtr(111)',), 'IntPtr(999)')
        
        self.assertFinds("PyCObject_FromVoidPtr", ('IntPtr(111)', 'IntPtr(222)'), 'IntPtr(999)')
        self.assertFinds("PyCObject_AsVoidPtr", ('IntPtr(111)',), 'IntPtr(999)')
        
        self.assertFinds("PyMem_Malloc", ('999',), 'IntPtr(12345)')
        self.assertFinds("PyMem_Free", ('IntPtr(999)',), 'None')
        
        self.assertFinds("PyThread_allocate_lock", tuple(), 'IntPtr(999)')
        self.assertFinds("PyThread_free_lock", ('IntPtr(123)',), 'None')
        self.assertFinds("PyThread_acquire_lock", ('IntPtr(123)', '1'), '1')
        self.assertFinds("PyThread_release_lock", ('IntPtr(123)',), 'None')
        
        self.assertFinds("PyThreadState_GetDict", tuple(), 'IntPtr(123)')
        
        self.assertFinds("PyEval_InitThreads", tuple(), 'None')


    def testPython25ApiImplementationOf_PyEval_SaveThread(self):
        self.assertEquals(Python25Api().PyEval_SaveThread(), IntPtr.Zero,
                          "unexpectedly wrong implementation")


    def testPython25ApiImplementationOf_PyEval_RestoreThread(self):
        Python25Api().PyEval_RestoreThread(IntPtr.Zero)
        # would have raised before getting here


    def testPython25ApiImplementationOf_PyEval_InitThreads(self):
        # I think I can get away with ignoring this function
        self.assertEquals(Python25Api().PyEval_InitThreads(), None)


suite = makesuite(
    Python25ApiTest,
    Python25ApiFunctionsTest
)

if __name__ == '__main__':
    run(suite)
