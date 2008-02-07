
import os
import sys
import unittest

from System import Console, IntPtr
from System.IO import StringWriter
from System.Runtime.InteropServices import Marshal

from JumPy import PydImporter


class PydImporterTest(unittest.TestCase):

    def testCallsAppropriatelyNamedInitFunctionAndUnloadsWhenDone(self):
        l = PydImporter.LoadLibrary("tests\\data\\setvalue.pyd")
        try:
            pValue = PydImporter.GetProcAddress(l, "value")
            value = Marshal.ReadInt32(pValue)
            self.assertEquals(value, 1, "bad setup")

            pi = PydImporter()
            pi.Load("tests\\data\\setvalue.pyd")
        finally:
            # lose test reference to setvalue.pyd
            # only the PydImporter should still have a reference to it
            PydImporter.FreeLibrary(l)

        value = Marshal.ReadInt32(pValue)
        self.assertEquals(value, 2, "PydImporter didn't call correct function")

        pi.Dispose()
        self.assertEquals(PydImporter.GetModuleHandle("setvalue.pyd"), IntPtr.Zero,
                          "failed to unload on dispose")


suite = unittest.TestSuite()
loader = unittest.TestLoader()
suite.addTest(loader.loadTestsFromTestCase(PydImporterTest))

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)