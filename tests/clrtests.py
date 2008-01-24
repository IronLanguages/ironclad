
import clr
clr.AddReferenceToFile("build/jumpy.dll")

import unittest
suite = unittest.TestSuite()

from tests import stubreferencetest
suite.addTest(stubreferencetest.suite)

from tests import pythonmappertest
suite.addTest(pythonmappertest.suite)

from tests import functionalitytest
#suite.addTest(functionalitytest.suite)

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)


