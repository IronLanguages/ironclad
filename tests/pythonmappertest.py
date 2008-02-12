
import unittest
from tests.utils.memory import OffsetPtr
from tests.utils.runtest import makesuite, run

from System import IntPtr
from System.Runtime.InteropServices import Marshal
from JumPy import CPyMarshal, PythonMapper, StubReference


def Write16Bytes(address):
    for a in range(4):
        ptr = OffsetPtr(address, a * CPyMarshal.IntSize)
        Marshal.WriteInt32(ptr, 1359)


def TestWrote16Bytes(address):
    for a in range(4):
        ptr = OffsetPtr(address, a * CPyMarshal.IntSize)
        data = Marshal.ReadInt32(ptr)
        if data != 1359:
            raise AssertionError("write failed")



class PythonMapperTest(unittest.TestCase):

    def testDataSetterDoesNotWriteForUnrecognisedSymbols(self):
        pm = PythonMapper()
        pm.SetData("This_symbol_is_not_exported_either_I_sincerely_hope", IntPtr.Zero)


    def assertDataSetterSets(self, mapperSubclass, dataSymbol, allocSize, memoryTest):
        dataPtr = Marshal.AllocHGlobal(allocSize)
        try:
            mapperSubclass().SetData(dataSymbol, dataPtr)
            memoryTest(dataPtr)
        finally:
            Marshal.FreeHGlobal(dataPtr)


    def testPythonMapperFinds_PyString_Type(self):
        class MyPM(PythonMapper):
            def Fill_PyString_Type(self, address):
                Write16Bytes(address)

        self.assertDataSetterSets(MyPM, "PyString_Type", 16, TestWrote16Bytes)


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


    def testPythonMapperFinds_PyString_FromString(self):
        paramsStore = []
        class MyPM(PythonMapper):
            def PyString_FromString(self, text):
                paramsStore.append((text, ))
                return IntPtr.Zero

        self.assertDispatches(
            MyPM, "PyString_FromString",
            ("name", ),
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


    def testPythonMapperImplementationOf_PyEval_SaveThread(self):
        self.assertEquals(PythonMapper().PyEval_SaveThread(), IntPtr.Zero,
                          "unexpectedly wrong implementation")


    def testPythonMapperImplementationOf_PyEval_RestoreThread(self):
        PythonMapper().PyEval_RestoreThread(IntPtr.Zero)
        # would have raised before getting here


suite = makesuite(PythonMapperTest)

if __name__ == '__main__':
    run(suite)