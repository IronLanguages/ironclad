
import unittest

from System import IntPtr
from System.Runtime.InteropServices import Marshal
from JumPy import PythonMapper, StubReference


class PythonMapperTest(unittest.TestCase):

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



suite = unittest.TestSuite()
loader = unittest.TestLoader()
suite.addTest(loader.loadTestsFromTestCase(PythonMapperTest))

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)