import sys
import math
from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase

class Number(object):
    def __long__(self):
        return 0L
    def __float__(self):
        return 0.0001

class BugTest(TestCase):

    def testDisplayhook(self):
        self.assertEquals(hasattr(sys, '__displayhook__'), False, "ironclad.py and Python25Mapper.MessWithSys may no longer need to set sys.__displayhook__ = sys.displayhook")

    def testLogWorksNow(self):
        math.log(Number())
        math.log10(Number())

    def testIterType(self):
        class C(object):
            def __iter__(self):
                yield 1
        
        iter(C)
        # when this fails, fix PySeqIter_New and PyObject_GetIter


suite = makesuite(BugTest)
if __name__ == '__main__':
    run(suite)