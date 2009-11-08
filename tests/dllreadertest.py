
from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase

from tools.dllreader import DllReader


class DllReaderTest(TestCase):

    def testInit(self):
        sm = DllReader('tests/data/exportsymbols.dll')
        self.assertEquals(sm.functions, ['Func', 'Funk', 'Jazz'])
        self.assertEquals(sm.data, ['Alphabetised', 'AnotherExportedSymbol', 'ExportedSymbol'])



suite = makesuite(
    DllReaderTest,
)

if __name__ == '__main__':
    run(suite)
