import sys
from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase

class BugTest(TestCase):
    def testDisplayhook(self):
        self.assertEquals(hasattr(sys, '__displayhook__'), False, "build/ironclad.py no longer needs to set sys.__displayhook__ = sys.displayhook")

suite = makesuite(BugTest)
if __name__ == '__main__':
    run(suite)