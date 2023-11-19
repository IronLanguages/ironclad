
import os
from tests.utils.runtest import makesuite, run

from tests.utils.gc import gcwait
from tests.utils.loadassemblies import CPYTHONSTUB_DLL
from tests.utils.testcase import TestCase

from Ironclad import dgt_getfuncptr, dgt_registerdata, Unmanaged, StubReference
from System import IntPtr

CPYTHONSTUB_DLL_NAME = os.path.basename(CPYTHONSTUB_DLL)

class StubReferenceTest(TestCase):

    def testMapInitUnmapLibrary(self):
        self.assertEqual(Unmanaged.GetModuleHandle(CPYTHONSTUB_DLL_NAME), IntPtr.Zero,
                          "library already mapped")

        sr = StubReference(CPYTHONSTUB_DLL)
        self.assertNotEqual(Unmanaged.GetModuleHandle(CPYTHONSTUB_DLL_NAME), IntPtr.Zero,
                          "library not mapped by construction")

        fpCalls = []
        @dgt_getfuncptr
        def GetFuncPtr(name):
            fpCalls.append(name)
            return IntPtr.Zero

        dataCalls = []
        @dgt_registerdata
        def RegisterData(name, _):
            dataCalls.append(name)

        sr.Init(GetFuncPtr, RegisterData)
        self.assertEqual(len(fpCalls) > 0, True, "did not get any addresses")
        self.assertEqual(len(dataCalls) > 0, True, "did not set any data")

        sr.Dispose()
        self.assertEqual(Unmanaged.GetModuleHandle(CPYTHONSTUB_DLL_NAME), IntPtr.Zero,
                          "library not unmapped on dispose")

        sr.Dispose()
        # safe to call Dispose twice
        
        
    def testUnmapsAutomagically(self):
        sr = StubReference(CPYTHONSTUB_DLL)
        self.assertNotEqual(Unmanaged.GetModuleHandle(CPYTHONSTUB_DLL_NAME), IntPtr.Zero,
                          "library not mapped by construction")
        del sr
        gcwait()
        self.assertEqual(Unmanaged.GetModuleHandle(CPYTHONSTUB_DLL_NAME), IntPtr.Zero,
                          "library not unmapped on finalize")
        

    def testLoadBuiltinModule(self):
        sr = StubReference(os.path.join(self.testDataBuildDir, "fakepython.dll"))
        sr.LoadBuiltinModule('somecrazymodule') # if func not found and callable, error
        sr.Dispose()
        



suite = makesuite(StubReferenceTest)
if __name__ == '__main__':
    run(suite)

