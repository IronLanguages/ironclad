
import os
import unittest

from System import GC, IntPtr
from System.Diagnostics import Process

from JumPy import AddressGetterDelegate, PythonMapper, StubReference

from JumPyTestUtils import PythonStubHarness


class PyArg_ParseTupleAndKeywordsLeakTest(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        class MyPM(PythonMapper):
            def PyArg_ParseTupleAndKeywords(self, args, kwargs, format, kwlist, argptr):
                return 1

        self.sr = StubReference(os.path.join("build", "python25.dll"))
        self.pm = MyPM()
        self.sr.Init(AddressGetterDelegate(self.pm.GetAddress))


    def tearDown(self):
        self.sr.Dispose()
        del self.pm


    def testProbablyDoesntLeak(self):
        # warning: brittle -- depends on current quantity of preallocated memory.
        # should be run in separate process to minimise interference from allocations
        # caused by other tests. also highly sensitive to changes in allocCount.
        allocCount = 5000

        GC.Collect()
        before = Process.GetCurrentProcess().VirtualMemorySize

        for _ in xrange(allocCount):
            PythonStubHarness.Test_PA_PTAK__3arg(
                IntPtr(1), IntPtr(2), "iii", IntPtr(3),
                IntPtr(100), IntPtr(200), IntPtr(300))

        GC.Collect()
        after = Process.GetCurrentProcess().VirtualMemorySize

        self.assertEquals(after - before, 0, "probably leaked; see comment")


suite = unittest.TestSuite()
loader = unittest.TestLoader()
suite.addTest(loader.loadTestsFromTestCase(PyArg_ParseTupleAndKeywordsLeakTest))

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)