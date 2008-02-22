
import unittest
from tests.utils.runtest import makesuite, run

from System import IntPtr

from Ironclad import CPyMarshal, PydImporter, Kernel32


class PydImporterTest(unittest.TestCase):

    def testCallsAppropriatelyNamedInitFunctionAndUnloadsWhenDone(self):
        l = Kernel32.LoadLibrary("tests\\data\\setvalue.pyd")
        try:
            pValue = Kernel32.GetProcAddress(l, "value")
            value = CPyMarshal.ReadInt(pValue)
            self.assertEquals(value, 1, "bad setup")

            pi = PydImporter()
            pi.Load("tests\\data\\setvalue.pyd")
        finally:
            # lose test reference to setvalue.pyd
            # only the PydImporter should still have a reference to it
            Kernel32.FreeLibrary(l)

        value = CPyMarshal.ReadInt(pValue)
        self.assertEquals(value, 2, "PydImporter didn't call correct function")

        pi.Dispose()
        self.assertEquals(Kernel32.GetModuleHandle("setvalue.pyd"), IntPtr.Zero,
                          "failed to unload on dispose")


suite = makesuite(PydImporterTest)

if __name__ == '__main__':
    run(suite)