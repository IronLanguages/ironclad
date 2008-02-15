
import tests.utils.loadassemblies

import os
import sys
import unittest
from tests.utils.runtest import makesuite, run

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


def RunSeparateProcessTest(testCase):
    result = run(makesuite(testCase))
    if not result.wasSuccessful():
        sys.exit(-1)