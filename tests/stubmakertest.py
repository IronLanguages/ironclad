
import unittest
from tests.utils.runtest import makesuite, run

from textwrap import dedent

from tools.stubmaker import StubMaker


class StubMakerInitTest(unittest.TestCase):

    def testInitEmpty(self):
        sm = StubMaker()
        self.assertEquals(sm.data, [], 'bad init')
        self.assertEquals(sm.functions, [], 'bad init')
        self.assertEquals(sm.overrides, {}, 'bad init')
        self.assertEquals(sm.postamble, '', 'bad init')


    def testInitCollects(self):
        sm = StubMaker('tests/data/exportsymbols.dll')
        self.assertEquals(sm.data, ['Alphabetised', 'AnotherExportedSymbol', 'ExportedSymbol'],
                          'found unexpected data symbols')
        self.assertEquals(sm.functions, ['Func', 'Funk', 'Jazz'],
                          'found unexpected code symbols')
        self.assertEquals(sm.overrides, {}, 'overrode unexpected symbols')
        self.assertEquals(sm.postamble, '', 'bad init')


    def testInitCollectsOverridesAndIgnoresIgnores(self):
        sm = StubMaker('tests/data/exportsymbols.dll', 'tests/data/overrides')
        self.assertEquals(sm.functions, ['Func', 'Jazz'],
                          'found unexpected code symbols')
        self.assertEquals(sm.data, ['Alphabetised', 'AnotherExportedSymbol', 'ExportedSymbol'],
                          'found unexpected data symbols')
        self.assertEquals(sm.overrides,
                          {'AnotherExportedSymbol':
                           '\nchar AnotherExportedSymbol[616];\n',
                           'Jazz':
                           '\nvoid Jazz() {\n    int I_can_has_jmp_to_elemants[%d];\n}\n'},
                          'overrode unexpected data symbols')
        self.assertEquals(sm.postamble, "\nvoid Funk(void) {\n    // arbitrary code\n}\n")


class StubMakerGenerateCTest(unittest.TestCase):

    def testGenerateCWritesBareMinimum(self):
        sm = StubMaker()
        sm.data = ['DATA', 'MOREDATA']
        sm.functions = ['FUNC', 'OVERRIDE']
        sm.overrides = {'OVERRIDE':
                        'void OVERRIDE() {\n    do something with jumptable[%d];\n}\n',
                        'MOREDATA':
                        'char MOREDATA[48];\n'}
        sm.postamble = '\nand some more code...\n'

        expected = dedent("""\
        #include <stdio.h>
        #include <stdarg.h>
        #include <stdlib.h>

        void *DATA;
        char MOREDATA[48];

        void *jumptable[2];

        void init(void*(*address_getter)(char*), void(*data_setter)(char*, void*)) {
            DATA = address_getter("DATA");
            data_setter("MOREDATA", &MOREDATA);
            jumptable[0] = address_getter("FUNC");
            jumptable[1] = address_getter("OVERRIDE");
        }

        void OVERRIDE() {
            do something with jumptable[1];
        }
        
        and some more code...
        """)
        result = sm.generate_c()
        self.assertEquals(result, expected, 'wrong output')


    def testGenerateCWritesVoidPointerData(self):
        sm = StubMaker()
        sm.data = ['Awesome', 'Awesome_to_the_max']

        expected = "void *Awesome;\nvoid *Awesome_to_the_max;\n"
        self.assertNotEquals(sm.generate_c().find(expected), -1,
                             'could not find expected output')


    def testGenerateCWritesOverrideData(self):
        sm = StubMaker()
        sm.data = ['Reason', 'Ultima_ratio_regum']
        sm.overrides = {'Reason':
                        'char Reason[32];\n',
                        'Ultima_ratio_regum':
                        'char Ultima_ratio_regum[192];\n'}

        result = sm.generate_c()

        expectedSnippets = (
            'char Reason[32];\n',
            'char Ultima_ratio_regum[192];\n',
            '    data_setter("Reason", &Reason);\n',
            '    data_setter("Ultima_ratio_regum", &Ultima_ratio_regum);\n',
        )
        for s in expectedSnippets:
            self.assertNotEquals(result.find(s), -1, 'could not find expected code')

        unexpectedSnippets = (
            'void *Reason;\n',
            'void *Ultima_ratio_regum;\n',
            '    Reason = address_getter("Reason");\n',
            '    Ultima_ratio_regum = address_getter("Ultima_ratio_regum");\n',
        )
        for s in unexpectedSnippets:
            self.assertEquals(result.find(s), -1, 'found unexpected code')


    def testGenerateCWritesJumpTableSize(self):
        sm = StubMaker()
        sm.functions = ['a', 'b', 'd', 'e']
        sm.overrides = {'b': '%d', 'e': '%d'}

        expected = "void *jumptable[4];\n"
        self.assertNotEquals(sm.generate_c().find(expected), -1,
                     'could not find expected output')


    def testGenerateCFillsJumpTable(self):
        sm = StubMaker()
        sm.functions = ['a', 'b', 'd', 'e']
        sm.overrides = {'b': '%d', 'e': '%d'}

        expected = dedent("""\
        void init(void*(*address_getter)(char*), void(*data_setter)(char*, void*)) {
            jumptable[0] = address_getter("a");
            jumptable[1] = address_getter("b");
            jumptable[2] = address_getter("d");
            jumptable[3] = address_getter("e");
        }""")
        self.assertNotEquals(sm.generate_c().find(expected), -1,
                     'could not find expected output')


    def testGenerateCCreatesOverrideFunctions(self):
        sm = StubMaker()
        sm.functions = ['a', 'b', 'd', 'e']
        sm.overrides = {'b': 'void b() { %d }\n', 'e': 'void e() { %d }\n'}

        expected = dedent("""\
        void b() { 1 }
        void e() { 3 }""")
        self.assertNotEquals(sm.generate_c().find(expected), -1,
                     'could not find expected output')



class StubMakerGenerateAsmTest(unittest.TestCase):

    def testGenerateAsmCreatesLabelsForNonOverriddenFunctions(self):
        sm = StubMaker()
        sm.data = ['not relevant']
        sm.functions = ['a', 'b', 'c', 'e']
        sm.overrides = {'b': 'whatever'}

        expected = dedent("""\
        extern _jumptable

        section .code

        global _a
        global _c
        global _e

        _a:
            jmp [_jumptable+0]
        _c:
            jmp [_jumptable+8]
        _e:
            jmp [_jumptable+12]""")
        self.assertNotEquals(sm.generate_asm().find(expected), -1,
                     'could not find expected output')


class StubMakerGenerateMakefileTest(unittest.TestCase):

    def testGenerateMakefile(self):
        sm = StubMaker()

        expected = (
            "stubname.dll: asm.o c.o\n"
            "\tgcc -shared -o stubname.dll asm.o c.o\n"
            "asm.o: stubname.asm\n"
            "\tnasm -o asm.o -f win32 stubname.asm\n"
            "c.o: stubname.c\n"
            "\tgcc -o c.o -c stubname.c\n"
        )
        self.assertEquals(sm.generate_makefile("stubname"), expected,
                          "wrong output")


suite = makesuite(
    StubMakerInitTest,
    StubMakerGenerateCTest,
    StubMakerGenerateAsmTest,
    StubMakerGenerateMakefileTest
)

if __name__ == '__main__':
    run(suite)
