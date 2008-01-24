
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


    def testPythonMapperFinds_Py_InitModule4(self):
        params = []
        class MyPM(PythonMapper):
            def Py_InitModule4(self, name, methods, doc, _self, apiver):
                params.append((name, methods, doc, _self, apiver))
                return IntPtr.Zero
        pm = MyPM()

        fp1 = pm.GetAddress("Py_InitModule4")
        self.assertNotEquals(fp1, IntPtr.Zero, "unexpected nullity")
        fp2 = pm.GetAddress("Py_InitModule4")
        self.assertEquals(fp1, fp2, "2 calls produced different pointers")

        dgt = Marshal.GetDelegateForFunctionPointer(fp1, PythonMapper.Py_InitModule4_Delegate)
        result = dgt("name", IntPtr.Zero, "doc", IntPtr.Zero, 12345)

        self.assertEquals(result, IntPtr.Zero, "unexpected return address")
        self.assertEquals(len(params), 1, "wrong number of calls")
        self.assertEquals(params[0], ("name", IntPtr.Zero, "doc", IntPtr.Zero, 12345),
                          "wrong params")


suite = unittest.TestSuite()
loader = unittest.TestLoader()
suite.addTest(loader.loadTestsFromTestCase(PythonMapperTest))

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)