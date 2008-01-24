
import os
import unittest

from System import IntPtr
from JumPy import AddressGetterDelegate, PythonMapper, StubReference



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
        pi.load("C:\\Python25\\Dlls\\_socket.pyd")

        name, methods, doc, _self, apiver = params[0]
        self.assertEquals(name, "_socket", "wrong name")
        self.assertNotEquals(methods, IntPtr.Zero, "expected some actual methods here")
        self.assertEquals(doc, "Implementation module for socket operations.\n\nSee the socket module for documentation.",
                          "wrong docstring")
        self.assertEquals(_self, IntPtr.Zero, "expected null pointer")
        self.assertEquals(apiver, 1012, "meh, thought this would be different")



suite = unittest.TestSuite()
loader = unittest.TestLoader()
suite.addTest(loader.loadTestsFromTestCase(FunctionalityTest))

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)


