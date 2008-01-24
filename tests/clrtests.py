
import clr
clr.AddReferenceToFile("build/jumpy.dll")

import unittest
suite = unittest.TestSuite()

from tests import stubreferencetest
suite.addTest(stubreferencetest.suite)

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)


