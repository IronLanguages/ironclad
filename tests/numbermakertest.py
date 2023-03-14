

from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase
from tests.utils.numbers import NumberI, NumberF, NUMBER_VALUE

from Ironclad import NumberMaker

class NumberMakerTest(TestCase):

    def testBigInteger(self):
        result = NumberMaker.MakeBigInteger(NumberI())
        self.assertEqual(isinstance(result, int), True)
        self.assertEqual(result, NUMBER_VALUE)

        self.assertRaises(TypeError, lambda: NumberMaker.MakeBigInteger(object()))

    def testUnsignedBigInteger(self):
        class NumberNeg(object):
            def __int__(self):
                return -1
        self.assertRaises(TypeError, lambda: NumberMaker.MakeUnsignedBigInteger(NumberNeg()))

        result = NumberMaker.MakeUnsignedBigInteger(NumberI())
        self.assertEqual(isinstance(result, int), True)
        self.assertEqual(result, NUMBER_VALUE)

    def testFloat(self):
        for cls in (NumberI, NumberF):
            result = NumberMaker.MakeFloat(cls())
            self.assertEqual(isinstance(result, float), True)
            self.assertEqual(result, NUMBER_VALUE)

        self.assertRaises(TypeError, lambda: NumberMaker.MakeFloat(object()))



suite = makesuite(NumberMakerTest)
if __name__ == '__main__':
    run(suite)
