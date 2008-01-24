
import unittest
suite = unittest.TestSuite()

from tests import stubmakertest
suite.addTest(stubmakertest.suite)

from tests import buildstubtest
suite.addTest(buildstubtest.suite)

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)