
import os
import unittest
from tests.utils.runtest import makesuite, run

from Ironclad import AddressGetterDelegate, DataSetterDelegate, Kernel32, StubReference
from System import IntPtr


class StubReferenceTest(unittest.TestCase):

    def testMapInitUnmapLibrary(self):
        self.assertEquals(Kernel32.GetModuleHandle("python25.dll"), IntPtr.Zero,
                          "library already mapped")

        sr = StubReference(os.path.join("build", "python25.dll"))
        self.assertNotEquals(Kernel32.GetModuleHandle("python25.dll"), IntPtr.Zero,
                          "library not mapped by construction")

        addressCalls = []
        def AddressGetter(name):
            addressCalls.append(name)
            return IntPtr.Zero

        dataCalls = []
        def DataSetter(name, _):
            dataCalls.append(name)

        sr.Init(AddressGetterDelegate(AddressGetter), DataSetterDelegate(DataSetter))
        self.assertEquals(len(addressCalls) > 0, True, "did not get any addresses")
        self.assertEquals(len(dataCalls) > 0, True, "did not set any data")

        sr.Dispose()
        self.assertEquals(Kernel32.GetModuleHandle("python25.dll"), IntPtr.Zero,
                          "library not unmapped on dispose")



suite = makesuite(StubReferenceTest)
if __name__ == '__main__':
    run(suite)

