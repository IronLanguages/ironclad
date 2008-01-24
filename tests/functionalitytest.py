
import os
import unittest

from System import IntPtr
from JumPy import AddressGetterDelegate, PydImporter, PythonMapper, StubReference



class FunctionalityTest(unittest.TestCase):

    def testCanCallbackIntoManagedCode(self):
        params = []

        class MyPM(PythonMapper):
            def Py_InitModule4(self, name, methods, doc, _self, apiver):
                params.append((name, methods, doc, _self, apiver))
                return IntPtr.Zero

        sr = StubReference(os.path.join("build", "python25.dll"))
        sr.Init(AddressGetterDelegate(MyPM().GetAddress))

        pi = PydImporter()
        pi.load("C:\\Python25\\Dlls\\bz2.pyd")

        name, methods, doc, _self, apiver = params[0]
        self.assertEquals(name, "bz2", "wrong name")
        self.assertNotEquals(methods, IntPtr.Zero, "expected some actual methods here")
        self.assertTrue(doc.startswith("The python bz2 module provides a comprehensive interface for\n"),
                        "wrong docstring")
        self.assertEquals(_self, IntPtr.Zero, "expected null pointer")
        self.assertEquals(apiver, 1013, "meh, thought this would be different")



suite = unittest.TestSuite()
loader = unittest.TestLoader()
suite.addTest(loader.loadTestsFromTestCase(FunctionalityTest))

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)


