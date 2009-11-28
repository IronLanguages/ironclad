

from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase
from tests.utils.numbers import NumberI, NumberL, NumberF, NUMBER_VALUE

from Ironclad import NumberMaker

class NumberMakerTest(TestCase):

    def testBigInteger(self):
        for cls in (NumberI, NumberL, NumberF):
            result = NumberMaker.MakeBigInteger(cls())
            self.assertEquals(isinstance(result, long), True)
            self.assertEquals(result, NUMBER_VALUE)

        self.assertRaises(TypeError, lambda: NumberMaker.MakeBigInteger(object()))

    def testUnsignedBigInteger(self):
        class NumberNeg(object):
            def __int__(self):
                return -1
        self.assertRaises(TypeError, lambda: NumberMaker.MakeUnsignedBigInteger(NumberNeg()))

        result = NumberMaker.MakeBigInteger(NumberF())
        self.assertEquals(isinstance(result, long), True)
        self.assertEquals(result, NUMBER_VALUE)

    def testFloat(self):
        for cls in (NumberI, NumberL, NumberF):
            result = NumberMaker.MakeFloat(cls())
            self.assertEquals(isinstance(result, float), True)
            self.assertEquals(result, NUMBER_VALUE)

        self.assertRaises(TypeError, lambda: NumberMaker.MakeFloat(object()))



suite = makesuite(NumberMakerTest)
if __name__ == '__main__':
    run(suite)