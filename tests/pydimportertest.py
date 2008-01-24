
import os
import sys
import unittest

from System import Console
from System.IO import StringWriter
from System.Runtime.InteropServices import Marshal

from JumPy import PydImporter


class PydImporterTest(unittest.TestCase):

    def testCallsAppropriatelyNamedInitFunction(self):
        l = PydImporter.LoadLibrary("tests\\data\\setvalue.pyd")
        pValue = PydImporter.GetProcAddress(l, "value")
        value = Marshal.ReadInt32(pValue)
        self.assertEquals(value, 1, "bad setup")

        pi = PydImporter()
        pi.load("tests\\data\\setvalue.pyd")

        value = Marshal.ReadInt32(pValue)
        self.assertEquals(value, 2, "PydImporter didn't call correct function")



suite = unittest.TestSuite()
loader = unittest.TestLoader()
suite.addTest(loader.loadTestsFromTestCase(PydImporterTest))

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)