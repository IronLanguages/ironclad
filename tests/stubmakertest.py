
from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase

from textwrap import dedent

from tools.stubmaker import StubMaker


class StubMakerInitTest(TestCase):

    def testInitEmpty(self):
        sm = StubMaker()
        self.assertEquals(sm.functions, [], 'bad init')
        self.assertEquals(sm.ptr_data, [], 'bad init')
        self.assertEquals(sm.static_data, [], 'bad init')


    def testInitCollects(self):
        sm = StubMaker('tests/data/exportsymbols.dll')
        self.assertEquals(sm.functions, ['Func', 'Funk', 'Jazz'],
                          'found unexpected code symbols')
        self.assertEquals(sm.ptr_data, ['Alphabetised', 'AnotherExportedSymbol', 'ExportedSymbol'],
                          'found unexpected data symbols')
        self.assertEquals(sm.static_data, [],
                          'moved data symbols unexpectedly')


    def testInitIgnoresIgnoresAndMovesStatics(self):
        sm = StubMaker('tests/data/exportsymbols.dll', 'tests/data/stub')
        self.assertEquals(sm.functions, ['Func', 'Jazz'],
                          'failed to remove ignored code symbols')
        self.assertEquals(sm.ptr_data, ['ExportedSymbol'],
                          'found unexpected data symbols')
        self.assertEquals(sm.static_data, ['AnotherExportedSymbol'],
                          'moved data symbols unexpectedly')


class StubMakerGenerateCTest(TestCase):

    def testGenerateCWritesBareMinimum(self):
        sm = StubMaker()
        sm.functions = ['FUNC1', 'FUNC2']
        sm.ptr_data = ['DATA1', 'DATA2']
        sm.static_data = ['DATA3', 'DATA4']

        expected = dedent("""\
        void *jumptable[2];

        void init(void*(*address_getter)(char*), void(*data_setter)(char*, void*)) {
            data_setter("DATA3", &DATA3);
            data_setter("DATA4", &DATA4);
            DATA1 = address_getter("DATA1");
            DATA2 = address_getter("DATA2");
            jumptable[0] = address_getter("FUNC1");
            jumptable[1] = address_getter("FUNC2");
        }
        """)
        result = sm.generate_c()
        self.assertEquals(result, expected, 'wrong output')


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



class StubMakerGenerateAsmTest(TestCase):

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
    StubMakerInitTest,
    StubMakerGenerateCTest,
    StubMakerGenerateAsmTest,
)

if __name__ == '__main__':
    run(suite)
