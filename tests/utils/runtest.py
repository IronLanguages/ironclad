
import unittest

def makesuite(*tests):
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for test in tests:
        suite.addTest(loader.loadTestsFromTestCase(test))
    return suite

def run(suite):
    return unittest.TextTestRunner().run(suite)

