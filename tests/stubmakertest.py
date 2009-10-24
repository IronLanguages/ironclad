
from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase

from textwrap import dedent

from tools.stubmaker import StubMaker


class StubMakerTest(TestCase):

    def testInitEmpty(self):
        sm = StubMaker()
        self.assertEquals(sm.functions, [], 'bad init')
        self.assertEquals(sm.mgd_functions, [], 'bad init')
        self.assertEquals(sm.data, set(), 'bad init')
        self.assertEquals(sm.ordered_data, [], 'bad init')


    def testInitCollects(self):
        sm = StubMaker('tests/data/exportsymbols.dll')
        self.assertEquals(sm.functions, ['Func', 'Funk', 'Jazz'])
        self.assertEquals(sm.data, set(['Alphabetised', 'AnotherExportedSymbol', 'ExportedSymbol']))


    def testInitIgnoresIgnoresAndAddsExtrasOrderedDataAndMgdFunctions(self):
        sm = StubMaker('tests/data/exportsymbols.dll', 'tests/data/stub')
        self.assertEquals(sm.functions, ['Func', 'Jazz', 'Bebop'])
        self.assertEquals(sm.mgd_functions, ['void Bebop(foo this, bar* that);'])
        self.assertEquals(sm.data, set(['ExportedSymbol', 'ExtraSymbol']))
        self.assertEquals(sm.ordered_data, ['MeFirst', 'AnotherExportedSymbol'])


    def testGenerateCWritesBareMinimum(self):
        sm = StubMaker()
        sm.functions = ['FUNC1', 'FUNC2']
        sm.mgd_functions = ['void FUNC2();']
        sm.data = ['DATA1', 'DATA2'] # list not set for reliable ordering in output
        sm.ordered_data = ['DATA3', 'DATA4']

        expected = dedent("""\
        void *jumptable[2];

        void init(void*(*address_getter)(char*), void(*data_setter)(char*, void*)) {
            data_setter("DATA3", &DATA3);
            data_setter("DATA4", &DATA4);
            data_setter("DATA1", &DATA1);
            data_setter("DATA2", &DATA2);
            jumptable[0] = address_getter("FUNC1");
            jumptable[1] = address_getter("FUNC2");
        }
        """)
        self.assertEquals(sm.generate_c(), expected)


    def testGenerateCWritesJumpTableSize(self):
        sm = StubMaker()
        sm.functions = ['a', 'b', 'd', 'e']

        expected = "void *jumptable[4];\n"
        self.assertNotEquals(sm.generate_c().find(expected), -1,
                     'could not find expected output')


    def testGenerateCFillsJumpTable(self):
        sm = StubMaker()
        sm.functions = ['a', 'b', 'd', 'e']

        expected = dedent("""\
        void init(void*(*address_getter)(char*), void(*data_setter)(char*, void*)) {
            jumptable[0] = address_getter("a");
            jumptable[1] = address_getter("b");
            jumptable[2] = address_getter("d");
            jumptable[3] = address_getter("e");
        }""")
        self.assertNotEquals(sm.generate_c().find(expected), -1,
                     'could not find expected output')


    def testGenerateHeader(self):
        sm = StubMaker()
        sm.mgd_functions = ['some', 'random stuff', 'blah blah blah']
        self.assertEquals(sm.generate_header(), '\n'.join(sm.mgd_functions) + '\n')


    def testGenerateAsmCreatesLabelsForNonOverriddenFunctions(self):
        sm = StubMaker()
        sm.functions = ['a', 'c', 'e']
        sm.ptr_data = ['not_relevant']
        sm.static_data = ['not_relevant_either']

        expected = dedent("""\
        extern _jumptable

        section .code

        global _a
        global _c
        global _e

        _a:
            jmp [_jumptable+0]
        _c:
            jmp [_jumptable+4]
        _e:
            jmp [_jumptable+8]""")
        self.assertNotEquals(sm.generate_asm().find(expected), -1,
                     'could not find expected output')


suite = makesuite(
    StubMakerTest,
)

if __name__ == '__main__':
    run(suite)
