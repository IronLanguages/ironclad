
import unittest
import tests.utils.loadassemblies

def makesuite(*tests):
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for test in tests:
        suite.addTest(loader.loadTestsFromTestCase(test))
    return suite

def run(suite, verbosity=1):
    return unittest.TextTestRunner(verbosity=verbosity).run(suite)

