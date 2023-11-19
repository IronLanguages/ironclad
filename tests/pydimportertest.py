
from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase

from tests.utils.gc import gcwait

from System import IntPtr

from Ironclad import CPyMarshal, PydImporter, Unmanaged


class PydImporterTest(TestCase):

    def testCallsAppropriatelyNamedInitFunctionAndUnloadsWhenDone(self):
        l = Unmanaged.LoadLibrary(self.testDataBuildDir + "\\setvalue.pyd")
        try:
            pValue = Unmanaged.GetProcAddress(l, "value")
            value = CPyMarshal.ReadInt(pValue)
            self.assertEqual(value, 1, "bad setup")

            pi = PydImporter()
            pi.Load(self.testDataBuildDir + "\\setvalue.pyd")
        finally:
            # lose test reference to setvalue.pyd
            # only the PydImporter should still have a reference to it
            Unmanaged.FreeLibrary(l)

        value = CPyMarshal.ReadInt(pValue)
        self.assertEqual(value, 2, "PydImporter didn't call correct function")

        pi.Dispose()
        self.assertEqual(Unmanaged.GetModuleHandle("setvalue.pyd"), IntPtr.Zero,
                          "failed to unload on dispose")

        pi.Dispose()
        # safe to call twice
    
    
    def testUnloadsAutomagically(self):
        pi = PydImporter()
        pi.Load(self.testDataBuildDir + "\\setvalue.pyd")
        del pi
        gcwait()
        self.assertEqual(Unmanaged.GetModuleHandle("setvalue.pyd"), IntPtr.Zero,
                          "failed to unload on dispose")
    

suite = makesuite(PydImporterTest)
if __name__ == '__main__':
    run(suite)
