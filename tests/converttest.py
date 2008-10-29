

from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase, WithMapper
from tests.utils.numbers import NumberI, NumberL, NumberF, NUMBER_VALUE

class ConvertTest(TestCase):

    @WithMapper
    def testBigInteger(self, mapper, _):
        for cls in (NumberI, NumberL, NumberF):
            result = mapper.MakeBigInteger(cls())
            self.assertEquals(isinstance(result, long), True)
            self.assertEquals(result, NUMBER_VALUE)

        self.assertRaises(TypeError, lambda: mapper.MakeBigInteger(object()))

    @WithMapper
    def testUnsignedBigInteger(self, mapper, _):
        class NumberNeg(object):
            def __int__(self):
                return -1
        self.assertRaises(TypeError, lambda: mapper.MakeUnsignedBigInteger(NumberNeg()))

        result = mapper.MakeBigInteger(NumberF())
        self.assertEquals(isinstance(result, long), True)
        self.assertEquals(result, NUMBER_VALUE)

    @WithMapper
    def testFloat(self, mapper, _):
        for cls in (NumberI, NumberL, NumberF):
            result = mapper.MakeFloat(cls())
            self.assertEquals(isinstance(result, float), True)
            self.assertEquals(result, NUMBER_VALUE)

        self.assertRaises(TypeError, lambda: mapper.MakeFloat(object()))



suite = makesuite(ConvertTest)
if __name__ == '__main__':
    run(suite)