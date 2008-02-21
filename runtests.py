import os
import clr
import unittest
from tests.utils.runtest import makesuite, run

clr.AddReferenceToFile("build/jumpy.dll")
clr.AddReference("IronPython.dll")
clr.AddReference("IronMath.dll")

def GetFailedImportTestSuite(name, e):
    class FailedImportTest(unittest.TestCase):
        def testFailedImport(self):
            raise Exception("could not import %s:\n%s" % (name, e))
    return makesuite(FailedImportTest)

suite = unittest.TestSuite()
for f in os.listdir("tests"):
    if f.endswith("test.py"):
        name = f[:-3]
        try:
            m = __import__("tests.%s" % name)
            suite.addTest(getattr(m, name).suite)
        except Exception, e:
            suite.addTest(GetFailedImportTestSuite(name, e))

if __name__ == '__main__':
    run(suite)