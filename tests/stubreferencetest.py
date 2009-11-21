
import os
from tests.utils.runtest import makesuite, run

from tests.utils.gc import gcwait
from tests.utils.testcase import TestCase

from Ironclad import dgt_getfuncptr, dgt_registerdata, Unmanaged, StubReference
from System import IntPtr

class StubReferenceTest(TestCase):

    def testMapInitUnmapLibrary(self):
        self.assertEquals(Unmanaged.GetModuleHandle("python26.dll"), IntPtr.Zero,
                          "library already mapped")

        sr = StubReference(os.path.join("build", "ironclad", "python26.dll"))
        self.assertNotEquals(Unmanaged.GetModuleHandle("python26.dll"), IntPtr.Zero,
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
        self.assertEquals(len(fpCalls) > 0, True, "did not get any addresses")
        self.assertEquals(len(dataCalls) > 0, True, "did not set any data")

        sr.Dispose()
        self.assertEquals(Unmanaged.GetModuleHandle("python26.dll"), IntPtr.Zero,
                          "library not unmapped on dispose")

        sr.Dispose()
        # safe to call Dispose twice
        
        
    def testUnmapsAutomagically(self):
        sr = StubReference(os.path.join("build", "ironclad", "python26.dll"))
        self.assertNotEquals(Unmanaged.GetModuleHandle("python26.dll"), IntPtr.Zero,
                          "library not mapped by construction")
        del sr
        gcwait()
        self.assertEquals(Unmanaged.GetModuleHandle("python26.dll"), IntPtr.Zero,
                          "library not unmapped on finalize")
        

    def testLoadBuiltinModule(self):
        sr = StubReference(os.path.join("tests", "data", "fakepython.dll"))
        sr.LoadBuiltinModule('somecrazymodule') # if func not found and callable, error
        sr.Dispose()
        



suite = makesuite(StubReferenceTest)
if __name__ == '__main__':
    run(suite)

