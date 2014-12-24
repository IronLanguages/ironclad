import sys
import math
from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase

from System import UInt32

class Number(object):
    def __long__(self):
        return 0L
    def __float__(self):
        return 0.0001

class BugTest(TestCase):

    def testLogWorksNow(self):
        math.log(Number())
        math.log10(Number())

    def testUIntLen(self):
        class C(object):
            def __len__(self):
                return UInt32(123)
        self.assertEquals(len(C()), 123, "uint len bug is back (are you using ipy 2.0 instead of 2.0.1?)")

suite = makesuite(BugTest)
if __name__ == '__main__':
    run(suite)
