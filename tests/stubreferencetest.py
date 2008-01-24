
import os
import unittest

from JumPy import AddressGetterDelegate, StubReference
from System import IntPtr
from System.Runtime.InteropServices import Marshal


class StubReferenceTest(unittest.TestCase):

    def testConstructMapsLibrary(self):
        self.assertEquals(StubReference.GetModuleHandle("python25.dll"), IntPtr.Zero,
                          "library already mapped")

        sr = StubReference(os.path.join("build", "python25.dll"))
        self.assertNotEquals(StubReference.GetModuleHandle("python25.dll"), IntPtr.Zero,
                          "library not mapped by construction")

        calls = []
        def AddressGetter(name):
            calls.append(name)
            return IntPtr.Zero

        sr.Init(AddressGetterDelegate(AddressGetter))
        self.assertEquals(len(calls), 904, "did not call once per symbol")

        sr.Dispose()
        self.assertEquals(StubReference.GetModuleHandle("python25.dll"), IntPtr.Zero,
                          "library not unmapped")



suite = unittest.TestSuite()
loader = unittest.TestLoader()
suite.addTest(loader.loadTestsFromTestCase(StubReferenceTest))

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)

