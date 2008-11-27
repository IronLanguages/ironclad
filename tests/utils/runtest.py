
import unittest
import tests.utils.loadassemblies

def automakesuite(symbols, excludes=[]):
    test_list = [value for (name, value) in symbols.iteritems()
        if isinstance(value, type) and issubclass(value, unittest.TestCase) and not value in excludes]
    return makesuite(*test_list)

def makesuite(*tests):
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for test in tests:
        suite.addTest(loader.loadTestsFromTestCase(test))
    return suite

def run(suite, verbosity=1):
    return unittest.TextTestRunner(verbosity=verbosity).run(suite)

