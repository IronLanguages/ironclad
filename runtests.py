import os
import unittest
import sys
from tests.utils.runtest import makesuite, run


def GetFailedImportTestSuite(name, e):
    class FailedImportTest(unittest.TestCase):
        def testFailedImport(self):
            raise Exception("could not import %s:\n%s" % (name, e))
    return makesuite(FailedImportTest)


def CreateSuite():
    suite = unittest.TestSuite()
    for f in os.listdir("tests"):
        if f.endswith("test.py"):
            name = f[:-3]
            try:
                print("adding: tests.%s" % name)
                m = __import__("tests.%s" % name)
                suite.addTest(getattr(m, name).suite)
            except Exception as e:
                suite.addTest(GetFailedImportTestSuite(name, e))
    return suite

# if run with a parameter, try to use it as a test selection (as
# specified in unittest, loadTestsFromName)
#
# Example 1 - run an individual test
# ipy runtests.py tests.baseobjecttest.NewInitFunctionsTest.test_PyObject_Newrun
#
# Example 2 - run all test from a module
# ipy runtests.py tests.itertest
#
# TODO: selecting decorated function does not work
if __name__ == '__main__':
    if 'IRONPYTHONPATH' not in os.environ:
        print("*"*80)
        print("WARNING: your IRONPYTHONPATH is not defined.")
        print("As absolute minimum, please set IRONPYTHONPATH=.")
        print("Some of ironclad test assume DLLs dir of cpython is present in IRONPYTHONPATH.")
        print("*"*80)
    if len(sys.argv) == 2:
        suite = unittest.defaultTestLoader.loadTestsFromName(sys.argv[1])
    else:
        suite = CreateSuite()

    run(suite, verbosity=2)
