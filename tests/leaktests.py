import os
import clr
clr.AddReferenceToFile("build/jumpy.dll")
clr.AddReferenceToFile("tests/data/jumpytestutils.dll")
clr.AddReference("IronPython.dll")
clr.AddReference("IronMath.dll")

import unittest
suite = unittest.TestSuite()

from tests import pyarg_parsetupleandkeywordsleaktest
suite.addTest(pyarg_parsetupleandkeywordsleaktest.suite)

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)


