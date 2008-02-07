
import clr
clr.AddReferenceToFile("build/jumpy.dll")
clr.AddReferenceToFile("tests/data/jumpytestutils.dll")
clr.AddReference("IronPython.dll")
clr.AddReference("IronMath.dll")

import os
import sys
import unittest

from System import GC, IntPtr
from System.Diagnostics import Process

from JumPy import AddressGetterDelegate, DataSetterDelegate, PythonMapper, StubReference


class LeakTestCase(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.sr = StubReference(os.path.join("build", "python25.dll"))
        self.pm = self.getPythonMapper()
        self.sr.Init(AddressGetterDelegate(self.pm.GetAddress),
                     DataSetterDelegate(self.pm.SetData))


    def tearDown(self):
        self.sr.Dispose()
        del self.pm


    def assertProbablyDoesntLeak(self, operation, count):
        # warning: brittle -- depends on current quantity of preallocated memory. Each
        # test should be run in separate process to minimise interference from unrelated
        # allocations; the mechanism is also highly sensitive to changes in count.

        GC.Collect()
        before = Process.GetCurrentProcess().VirtualMemorySize

        for _ in xrange(count):
            operation()

        GC.Collect()
        after = Process.GetCurrentProcess().VirtualMemorySize

        self.assertEquals(after - before, 0, "probably leaked; see comment")


def RunLeakTest(testCase):
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    suite.addTest(loader.loadTestsFromTestCase(testCase))
    if not unittest.TextTestRunner().run(suite).wasSuccessful():
        sys.exit(-1)