
from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase, WithMapper

from System import IntPtr

from types import MethodType

class MethodTest(TestCase):

    @WithMapper
    def testPyMethod_New(self, mapper, _):
        # if Python doesn't care what you put in a bound method, nor do I
        methPtr = mapper.PyMethod_New(IntPtr.Zero, IntPtr.Zero, IntPtr.Zero)
        self.assertEquals(mapper.Retrieve(methPtr), MethodType(None, None, None))
        self.assertMapperHasError(mapper, None)

        methPtr = mapper.PyMethod_New(mapper.Store(1), mapper.Store(2), mapper.Store(3))
        self.assertEquals(mapper.Retrieve(methPtr), MethodType(1, 2, 3))
        self.assertMapperHasError(mapper, None)



suite = makesuite(MethodTest)
if __name__ == '__main__':
    run(suite)