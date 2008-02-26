
import unittest
from tests.utils.memory import OffsetPtr
from tests.utils.runtest import makesuite, run

from System import IntPtr
from System.Runtime.InteropServices import Marshal
from Ironclad import CPyMarshal, PythonMapper

testNumber = 1359

def Write16Bytes(address):
    for a in range(4):
        ptr = OffsetPtr(address, a * CPyMarshal.IntSize)
        Marshal.WriteInt32(ptr, testNumber)


def TestWrote16Bytes(address):
    for a in range(4):
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


    def testPythonMapperFinds_PyString_Type(self):
        class MyPM(PythonMapper):
            def Fill_PyString_Type(self, address):
                Write16Bytes(address)
        self.assertDataSetterSetsAndRemembers(MyPM, "PyString_Type", 16, TestWrote16Bytes)


    def testPythonMapperFinds_PyType_Type(self):
        class MyPM(PythonMapper):
            def Fill_PyType_Type(self, address):
                Write16Bytes(address)
        self.assertDataSetterSetsAndRemembers(MyPM, "PyType_Type", 16, TestWrote16Bytes)


    def testPythonMapperFinds_PyFile_Type(self):
        class MyPM(PythonMapper):
            def Fill_PyFile_Type(self, address):
                Write16Bytes(address)
        self.assertDataSetterSetsAndRemembers(MyPM, "PyFile_Type", 16, TestWrote16Bytes)


    def testPythonMapperFinds_PyTuple_Type(self):
        class MyPM(PythonMapper):
            def Fill_PyTuple_Type(self, address):
                Write16Bytes(address)
        self.assertDataSetterSetsAndRemembers(MyPM, "PyTuple_Type", 16, TestWrote16Bytes)


    def testPythonMapperFinds_PyList_Type(self):
        class MyPM(PythonMapper):
            def Fill_PyList_Type(self, address):
                Write16Bytes(address)
        self.assertDataSetterSetsAndRemembers(MyPM, "PyList_Type", 16, TestWrote16Bytes)


    def testPythonMapperFinds_PyDict_Type(self):
        class MyPM(PythonMapper):
            def Fill_PyDict_Type(self, address):
                Write16Bytes(address)
        self.assertDataSetterSetsAndRemembers(MyPM, "PyDict_Type", 16, TestWrote16Bytes)


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


    def testPythonMapperFinds_PyArg_ParseTuple(self):
        paramsStore = []
        class MyPM(PythonMapper):
            def PyArg_ParseTuple(self, args, format, argsPtr):
                paramsStore.append((args, format, argsPtr))
                return True

        self.assertDispatches(
            MyPM, "PyArg_ParseTuple",
            (IntPtr(33), "format", IntPtr(1234)),
            True, paramsStore)


    def testPythonMapperFinds_PyArg_ParseTupleAndKeywords(self):
        paramsStore = []
        class MyPM(PythonMapper):
            def PyArg_ParseTupleAndKeywords(self, args, kwargs, format, kwlist, argsPtr):
                paramsStore.append((args, kwargs, format, kwlist, argsPtr))
                return True

        self.assertDispatches(
            MyPM, "PyArg_ParseTupleAndKeywords",
            (IntPtr(33), IntPtr(95), "format", IntPtr(63), IntPtr(1234)),
            True, paramsStore)


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




    def testPythonMapperImplementationOf_PyEval_SaveThread(self):
        self.assertEquals(PythonMapper().PyEval_SaveThread(), IntPtr.Zero,
                          "unexpectedly wrong implementation")


    def testPythonMapperImplementationOf_PyEval_RestoreThread(self):
        PythonMapper().PyEval_RestoreThread(IntPtr.Zero)
        # would have raised before getting here


suite = makesuite(PythonMapperTest)

if __name__ == '__main__':
    run(suite)