import os
import unittest

class LeakTest(unittest.TestCase):

    def testLeaks(self):
        failures = []
        path = os.path.join("tests", "leaktests")
        for f in os.listdir(path):
            if f.endswith("test.py"):
                if os.spawnl(os.P_WAIT, "ipy", "ipy", os.path.join(path, f)):
                    failures.append(f)
        self.assertEquals(failures, [], "leak tests failed:\n%s" % '\n'.join(failures))


suite = unittest.TestSuite()
loader = unittest.TestLoader()
suite.addTest(loader.loadTestsFromTestCase(LeakTest))
if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)

