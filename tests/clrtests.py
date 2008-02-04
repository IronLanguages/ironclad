import os
import clr
clr.AddReferenceToFile("build/jumpy.dll")
clr.AddReference("IronPython.dll")
clr.AddReference("IronMath.dll")

import unittest
suite = unittest.TestSuite()

from tests import stubreferencetest
suite.addTest(stubreferencetest.suite)

from tests import pydimportertest
suite.addTest(pydimportertest.suite)

from tests import pythonmappertest
suite.addTest(pythonmappertest.suite)

from tests import argwriterstest
suite.addTest(argwriterstest.suite)

from tests import python25structstest
suite.addTest(python25structstest.suite)

from tests import python25mappertest
suite.addTest(python25mappertest.suite)

from tests import functionalitytest
suite.addTest(functionalitytest.suite)

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)


