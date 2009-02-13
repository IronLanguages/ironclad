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

    def testLog10FloatMixin(self):
        class Floatish(float, object):
            pass
        num = Floatish(100.0)
        self.assertRaises(TypeError, lambda: math.log10(num))
        # when this fails stop patching log10 in import_code.py

    def testLongFromEmptyString(self):
        for str_ in ('', '   '):
            self.assertEquals(long(str_), 0, "you can fix PyNumber_Long now")

    def testUIntLen(self):
        class C(object):
            def __len__(self):
                return UInt32(123)
        self.assertRaises(TypeError, len, C())
        # when this fails, delete all references to LEN_TEMPLATE_TEMPLATE


suite = makesuite(BugTest)
if __name__ == '__main__':
    run(suite)