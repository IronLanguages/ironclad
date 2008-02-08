import os
import unittest
from tests.utils.runtest import makesuite, run

class LeakTest(unittest.TestCase):

    def testLeaks(self):
        print "\nRunning separate-process tests:"
        failures = []
        path = os.path.join("tests", "leaktests")
        for f in os.listdir(path):
            if f.endswith("test.py"):
                if os.spawnl(os.P_WAIT, "ipy", "ipy", os.path.join(path, f)):
                    failures.append(f)
        self.assertEquals(failures, [], "leak tests failed:\n%s" % '\n'.join(failures))


suite = makesuite(LeakTest)
if __name__ == '__main__':
    run(suite)

