import os
from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase

from tests.utils.gc import gcwait

from System import IntPtr

from Ironclad import CPyMarshal, PydImporter, Unmanaged


class PydImporterTest(TestCase):

    def testCallsAppropriatelyNamedInitFunctionAndUnloadsWhenDone(self):
        setvalue_mod = os.path.join(self.testDataBuildDir, "setvalue.pyd")
        l = Unmanaged.LoadLibrary(setvalue_mod)
        try:
            pValue = Unmanaged.GetProcAddress(l, "value")
            value = CPyMarshal.ReadInt(pValue)
            self.assertEqual(value, 1, "bad setup")

            pi = PydImporter()
            pi.Load(setvalue_mod)
        finally:
            # lose test reference to setvalue.pyd
            # only the PydImporter should still have a reference to it
            Unmanaged.FreeLibrary(l)

        value = CPyMarshal.ReadInt(pValue)
        self.assertEqual(value, 2, "PydImporter didn't call correct function")

        pi.Dispose()
        self.assertIsLibraryNotLoaded(setvalue_mod,
                          "failed to unload on dispose")

        pi.Dispose()
        # safe to call twice
    
    
    def testUnloadsAutomagically(self):
        pi = PydImporter()
        setvalue_mod = os.path.join(self.testDataBuildDir, "setvalue.pyd")
        pi.Load(setvalue_mod)
        del pi
        gcwait()
        self.assertIsLibraryNotLoaded(setvalue_mod,
                          "failed to unload on dispose")
    

suite = makesuite(PydImporterTest)
if __name__ == '__main__':
    run(suite)
