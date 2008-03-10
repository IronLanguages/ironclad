
import unittest
from tests.utils.memory import OffsetPtr
from tests.utils.runtest import makesuite, run

from System import IntPtr
from System.Runtime.InteropServices import Marshal
from Ironclad import CPyMarshal, PythonMapper
from Ironclad.Structs import PyTypeObject

testNumber = 1359
intCount = Marshal.SizeOf(PyTypeObject) / CPyMarshal.IntSize

def WritePyTypeObject(address):
    for a in range(intCount):
        ptr = OffsetPtr(address, a * CPyMarshal.IntSize)
        Marshal.WriteInt32(ptr, testNumber)

def TestWrotePyTypeObject(address):
    for a in range(intCount):
        ptr = OffsetPtr(address, a * CPyMarshal.IntSize)
        data = Marshal.ReadInt32(ptr)
        if data != testNumber:
            raise AssertionError("write failed")


class PythonMapperTest(unittest.TestCase):

    def testDataSetterDoesNotWriteForUnrecognisedSymbols(self):
        pm = PythonMapper()
        pm.SetData("This_symbol_is_not_exported_either_I_sincerely_hope", IntPtr.Zero)
        # had we written to IntPtr.Zero, we would have crashed


    def assertDataSetterSetsAndRemembers(self, mapperSubclass, dataSymbol, allocSize, memoryTest):
        dataPtr = Marshal.AllocHGlobal(allocSize)
        try:
            mapper = mapperSubclass()
            mapper.SetData(dataSymbol, dataPtr)
            memoryTest(dataPtr)
            self.assertEquals(getattr(mapper, dataSymbol), dataPtr, "failed to remember pointer")
        finally:
            Marshal.FreeHGlobal(dataPtr)


    def assertFindsType(self, name):
        class MyPM(PythonMapper):
            def fillmethod(self, address):
                WritePyTypeObject(address)
        setattr(MyPM, "Fill_" + name, getattr(MyPM, "fillmethod"))
        self.assertDataSetterSetsAndRemembers(MyPM, name, Marshal.SizeOf(PyTypeObject), TestWrotePyTypeObject)

    def testFindsTypes(self):
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
            "_PyWeakref_CallableProxyType",
        )
        for _type in _types:
            self.assertFindsType(_type)


    def assertAddressGetterRemembers(self, mapperSubclass, name, expectedAddress):
        pm = mapperSubclass()

        ptr = pm.GetAddress(name)
        self.assertEquals(ptr, expectedAddress, "unexpected result")
        self.assertEquals(getattr(pm, name), ptr, "did not remember")


    def testPythonMapperFinds_PyExc_SystemError(self):
        class MyPM(PythonMapper):
            def Make_PyExc_SystemError(self):
                return IntPtr(999)
        self.assertAddressGetterRemembers(MyPM, "PyExc_SystemError", IntPtr(999))


    def testPythonMapperFinds_PyExc_OverflowError(self):
        class MyPM(PythonMapper):
            def Make_PyExc_OverflowError(self):
                return IntPtr(999)
        self.assertAddressGetterRemembers(MyPM, "PyExc_OverflowError", IntPtr(999))


    def testAddressGetterFailsCleanly(self):
        pm = PythonMapper()
        addressGetter = pm.GetAddress

        self.assertEquals(addressGetter("This_symbol_is_not_exported_by_any_version_of_Python_so_far_as_I_know"),
                          IntPtr.Zero,
                          "bad result for nonsense symbol")


    def assertDispatches(self, mapperSubclass, funcName, argTuple, expectedResult, paramsStore):
        pm = mapperSubclass()

        fp1 = pm.GetAddress(funcName)
        self.assertNotEquals(fp1, IntPtr.Zero, "unexpected nullity")
        fp2 = pm.GetAddress(funcName)
        self.assertEquals(fp1, fp2, "2 calls produced different pointers")

        dgt = Marshal.GetDelegateForFunctionPointer(fp1, getattr(PythonMapper, funcName + "_Delegate"))
        result = dgt(*argTuple)

        self.assertEquals(result, expectedResult, "unexpected result")
        self.assertEquals(len(paramsStore), 1, "wrong number of calls")
        self.assertEquals(paramsStore[0], argTuple, "wrong params stored")


    def testPythonMapperFinds_Py_InitModule4(self):
        paramsStore = []
        class MyPM(PythonMapper):
            def Py_InitModule4(self, name, methods, doc, _self, apiver):
                paramsStore.append((name, methods, doc, _self, apiver))
                return IntPtr.Zero

        self.assertDispatches(
            MyPM, "Py_InitModule4",
            ("name", IntPtr.Zero, "doc", IntPtr.Zero, 12345),
            IntPtr.Zero, paramsStore)


    def testPythonMapperFinds_PyModule_AddObject(self):
        paramsStore = []
        class MyPM(PythonMapper):
            def PyModule_AddObject(self, module, name, item):
                paramsStore.append((module, name, item))
                return 33

        self.assertDispatches(
            MyPM, "PyModule_AddObject",
            (IntPtr(33), "henry", IntPtr(943)),
            33, paramsStore)


    def testPythonMapperFinds_PyModule_GetDict(self):
        paramsStore = []
        class MyPM(PythonMapper):
            def PyModule_GetDict(self, modulePtr):
                paramsStore.append((modulePtr,))
                return IntPtr(33)

        self.assertDispatches(
            MyPM, "PyModule_GetDict",
            (IntPtr(943),),
            IntPtr(33), paramsStore)


    def testPythonMapperFinds_PyString_FromString(self):
        paramsStore = []
        class MyPM(PythonMapper):
            def PyString_FromString(self, data):
                paramsStore.append((data, ))
                return IntPtr.Zero

        self.assertDispatches(
            MyPM, "PyString_FromString",
            (IntPtr(333), ),
            IntPtr.Zero, paramsStore)


    def testPythonMapperFinds_PyString_FromStringAndSize(self):
        paramsStore = []
        class MyPM(PythonMapper):
            def PyString_FromStringAndSize(self, stringPtr, size):
                paramsStore.append((stringPtr, size))
                return IntPtr(12345)

        self.assertDispatches(
            MyPM, "PyString_FromStringAndSize",
            (IntPtr(98765), 33),
            IntPtr(12345), paramsStore)


    def testPythonMapperFinds__PyString_Resize(self):
        paramsStore = []
        class MyPM(PythonMapper):
            def _PyString_Resize(self, stringPtrPtr, size):
                paramsStore.append((stringPtrPtr, size))
                return 0

        self.assertDispatches(
            MyPM, "_PyString_Resize",
            (IntPtr(98765), 33),
            0, paramsStore)


    def testPythonMapperFinds_PyErr_SetString(self):
        paramsStore = []
        class MyPM(PythonMapper):
            def PyErr_SetString(self, error, message):
                paramsStore.append((error, message))

        self.assertDispatches(
            MyPM, "PyErr_SetString",
            (IntPtr(98765), "and in the darkness bind them"),
            None, paramsStore)


    def testPythonMapperFinds_PyErr_Occurred(self):
        paramsStore = []
        class MyPM(PythonMapper):
            def PyErr_Occurred(self):
                paramsStore.append(tuple())
                return IntPtr(123)

        self.assertDispatches(
            MyPM, "PyErr_Occurred",
            tuple(),
            IntPtr(123), paramsStore)


    def testPythonMapperFinds_PyType_GenericNew(self):
        paramsStore = []
        class MyPM(PythonMapper):
            def PyType_GenericNew(self, typePtr, args, kwargs):
                paramsStore.append((typePtr, args, kwargs))
                return IntPtr(999)

        self.assertDispatches(
            MyPM, "PyType_GenericNew",
            (IntPtr(111), IntPtr(222), IntPtr(333)),
            IntPtr(999), paramsStore)


    def testPythonMapperFinds_PyType_GenericAlloc(self):
        paramsStore = []
        class MyPM(PythonMapper):
            def PyType_GenericAlloc(self, typePtr, nItems):
                paramsStore.append((typePtr, nItems))
                return IntPtr(999)

        self.assertDispatches(
            MyPM, "PyType_GenericAlloc",
            (IntPtr(111), 22),
            IntPtr(999), paramsStore)


    def testPythonMapperFinds_PyThread_allocate_lock(self):
        paramsStore = []
        class MyPM(PythonMapper):
            def PyThread_allocate_lock(self):
                paramsStore.append(tuple())
                return IntPtr(999)

        self.assertDispatches(
            MyPM, "PyThread_allocate_lock",
            tuple(),
            IntPtr(999), paramsStore)


    def testPythonMapperFinds_PyThread_free_lock(self):
        paramsStore = []
        class MyPM(PythonMapper):
            def PyThread_free_lock(self, ptr):
                paramsStore.append((ptr,))

        self.assertDispatches(
            MyPM, "PyThread_free_lock",
            (IntPtr(123),),
            None, paramsStore)


    def testPythonMapperFinds_PyThread_acquire_lock(self):
        paramsStore = []
        class MyPM(PythonMapper):
            def PyThread_acquire_lock(self, ptr, flags):
                paramsStore.append((ptr, flags))
                return 1

        self.assertDispatches(
            MyPM, "PyThread_acquire_lock",
            (IntPtr(123), 1),
            1, paramsStore)


    def testPythonMapperFinds_PyThread_release_lock(self):
        paramsStore = []
        class MyPM(PythonMapper):
            def PyThread_release_lock(self, ptr):
                paramsStore.append((ptr,))

        self.assertDispatches(
            MyPM, "PyThread_release_lock",
            (IntPtr(123),),
            None, paramsStore)


    def testPythonMapperFinds_PyObject_Call(self):
        paramsStore = []
        class MyPM(PythonMapper):
            def PyObject_Call(self, kallable, args, kwargs):
                paramsStore.append((kallable, args, kwargs))
                return IntPtr(999)

        self.assertDispatches(
            MyPM, "PyObject_Call",
            (IntPtr(123), IntPtr(456), IntPtr(789)),
            IntPtr(999), paramsStore)


    def testPythonMapperFinds_PyDict_New(self):
        paramsStore = []
        class MyPM(PythonMapper):
            def PyDict_New(self):
                paramsStore.append(tuple())
                return IntPtr(999)

        self.assertDispatches(
            MyPM, "PyDict_New",
            tuple(),
            IntPtr(999), paramsStore)


    def testPythonMapperFinds_PyDict_Size(self):
        paramsStore = []
        class MyPM(PythonMapper):
            def PyDict_Size(self, _dict):
                paramsStore.append((_dict,))
                return 999

        self.assertDispatches(
            MyPM, "PyDict_Size",
            (IntPtr(111),),
            999, paramsStore)


    def testPythonMapperFinds_PyDict_GetItemString(self):
        paramsStore = []
        class MyPM(PythonMapper):
            def PyDict_GetItemString(self, _dict, key):
                paramsStore.append((_dict, key))
                return IntPtr(999)

        self.assertDispatches(
            MyPM, "PyDict_GetItemString",
            (IntPtr(111), "boojum"),
            IntPtr(999), paramsStore)


    def testPythonMapperFinds_PyList_New(self):
        paramsStore = []
        class MyPM(PythonMapper):
            def PyList_New(self, size):
                paramsStore.append((size,))
                return IntPtr(999)

        self.assertDispatches(
            MyPM, "PyList_New",
            (33,),
            IntPtr(999), paramsStore)


    def testPythonMapperFinds_PyTuple_New(self):
        paramsStore = []
        class MyPM(PythonMapper):
            def PyTuple_New(self, size):
                paramsStore.append((size,))
                return IntPtr(999)

        self.assertDispatches(
            MyPM, "PyTuple_New",
            (33,),
            IntPtr(999), paramsStore)


    def testPythonMapperFinds_PyInt_FromLong(self):
        paramsStore = []
        class MyPM(PythonMapper):
            def PyInt_FromLong(self, value):
                paramsStore.append((value,))
                return IntPtr(999)

        self.assertDispatches(
            MyPM, "PyInt_FromLong",
            (33,),
            IntPtr(999), paramsStore)


    def testPythonMapperFinds_PyInt_FromSsize_t(self):
        paramsStore = []
        class MyPM(PythonMapper):
            def PyInt_FromSsize_t(self, value):
                paramsStore.append((value,))
                return IntPtr(999)

        self.assertDispatches(
            MyPM, "PyInt_FromSsize_t",
            (33,),
            IntPtr(999), paramsStore)


    def testPythonMapperFinds_PyFloat_FromDouble(self):
        paramsStore = []
        class MyPM(PythonMapper):
            def PyFloat_FromDouble(self, value):
                paramsStore.append((value,))
                return IntPtr(999)

        self.assertDispatches(
            MyPM, "PyFloat_FromDouble",
            (33.3,),
            IntPtr(999), paramsStore)


    def testPythonMapperFinds_PyFile_AsFile(self):
        paramsStore = []
        class MyPM(PythonMapper):
            def PyFile_AsFile(self, _file):
                paramsStore.append((_file,))
                return IntPtr(999)

        self.assertDispatches(
            MyPM, "PyFile_AsFile",
            (IntPtr(111),),
            IntPtr(999), paramsStore)


    def testPythonMapperFinds_PyObject_GetAttrString(self):
        paramsStore = []
        class MyPM(PythonMapper):
            def PyObject_GetAttrString(self, obj, name):
                paramsStore.append((obj, name))
                return IntPtr(999)

        self.assertDispatches(
            MyPM, "PyObject_GetAttrString",
            (IntPtr(111), "harold"),
            IntPtr(999), paramsStore)


    def testPythonMapperFinds_PyCallable_Check(self):
        paramsStore = []
        class MyPM(PythonMapper):
            def PyCallable_Check(self, obj):
                paramsStore.append((obj,))
                return 0

        self.assertDispatches(
            MyPM, "PyCallable_Check",
            (IntPtr(111),),
            0, paramsStore)




    def testPythonMapperImplementationOf_PyEval_SaveThread(self):
        self.assertEquals(PythonMapper().PyEval_SaveThread(), IntPtr.Zero,
                          "unexpectedly wrong implementation")


    def testPythonMapperImplementationOf_PyEval_RestoreThread(self):
        PythonMapper().PyEval_RestoreThread(IntPtr.Zero)
        # would have raised before getting here


suite = makesuite(PythonMapperTest)

if __name__ == '__main__':
    run(suite)