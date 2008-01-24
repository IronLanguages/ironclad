
import unittest
import sys

from textwrap import dedent

from tools.stubmaker import StubMaker


class StubMakerInitTest(unittest.TestCase):

    def testInitDetectsEnvironment(self):
        sm = StubMaker()
        if sys.platform.startswith('linux'):
            self.assertEquals(sm.platform, 'linux', 'wrong platform')
        elif sys.platform == 'win32':
            self.assertEquals(sm.platform, 'win32', 'wrong platform')
        else:
            self.fail('unknown environment')
        self.assertEquals(sm.data, [], 'bad init')
        self.assertEquals(sm.functions, [], 'bad init')
        self.assertEquals(sm.overrides, {}, 'bad init')

    def testInitCollectsData(self):
        sm = StubMaker('tests/data/exportsymbols.dll')
        self.assertEquals(sm.data, ['Alphabetised', 'AnotherExportedSymbol', 'ExportedSymbol'],
                          'found unexpected data symbols')


    def testInitCollectsFunctions(self):
        sm = StubMaker('tests/data/exportsymbols.dll')
        self.assertEquals(sm.functions, ['Func', 'Funk', 'Jazz'],
                          'found unexpected code symbols')
        self.assertEquals(sm.overrides, {}, 'overrode unexpected code symbols')


    def testInitCollectsOverrides(self):
        sm = StubMaker('tests/data/exportsymbols.dll', 'tests/data/overrides')
        self.assertEquals(sm.functions, ['Func', 'Funk', 'Jazz'],
                          'found unexpected code symbols')
        self.assertEquals(sm.overrides, {'Jazz': '\nvoid Jazz() {\n    int I_can_has_jmp_to_elemants[%d];\n}\n'},
                          'overrode unexpected code symbols')



class StubMakerGenerateCTest(unittest.TestCase):

    def testGenerateCWritesBareMinimum(self):
        sm = StubMaker()
        sm.data = ['DATA']
        sm.functions = ['FUNC', 'OVERRIDE']
        sm.overrides = {'OVERRIDE':
                        'void OVERRIDE() {\n    do something with jumptable[%d];\n}\n'}

        expected = dedent("""\
        #include <stdio.h>
        #include <stdarg.h>
        #include <stdlib.h>

        void *DATA;

        void *jumptable[2];

        void init(void*(*address_getter)(char*)) {
            DATA = address_getter("DATA");
            jumptable[0] = address_getter("FUNC");
            jumptable[1] = address_getter("OVERRIDE");
        }

        void OVERRIDE() {
            do something with jumptable[1];
        }
        """)
        self.assertEquals(sm.generate_c(), expected,
                          'wrong output')


    def testGenerateCWritesVoidPointerData(self):
        sm = StubMaker()
        sm.data = ['Awesome', 'Awesome_to_the_max']

        expected = "void *Awesome;\nvoid *Awesome_to_the_max;\n"
        self.assertNotEquals(sm.generate_c().find(expected), -1,
                             'could not find expected output')


    def testGenerateCWritesJumpTableSize(self):
        sm = StubMaker()
        sm.functions = ['a', 'b', 'c', 'd', 'e']
        sm.overrides = {'b': '%d', 'e': '%d'}

        expected = "void *jumptable[5];\n"
        self.assertNotEquals(sm.generate_c().find(expected), -1,
                     'could not find expected output')


    def testGenerateCFillsJumpTable(self):
        sm = StubMaker()
        sm.functions = ['a', 'b', 'c', 'd', 'e']
        sm.overrides = {'b': '%d', 'e': '%d'}

        expected = dedent("""\
        void init(void*(*address_getter)(char*)) {
            jumptable[0] = address_getter("a");
            jumptable[1] = address_getter("b");
            jumptable[2] = address_getter("c");
            jumptable[3] = address_getter("d");
            jumptable[4] = address_getter("e");
        }""")
        self.assertNotEquals(sm.generate_c().find(expected), -1,
                     'could not find expected output')


    def testGenerateCCreatesOverrideFunctions(self):
        sm = StubMaker()
        sm.functions = ['a', 'b', 'c', 'd', 'e']
        sm.overrides = {'b': 'void b() { %d }\n', 'e': 'void e() { %d }\n'}

        expected = dedent("""\
        void b() { 1 }
        void e() { 4 }""")
        self.assertNotEquals(sm.generate_c().find(expected), -1,
                     'could not find expected output')



class StubMakerGenerateAsmTest(unittest.TestCase):

    def testGenerateAsmCreatesLabelsForNonOverriddenFunctions(self):
        sm = StubMaker()
        sm.data = ['not relevant']
        sm.functions = ['a', 'b', 'c', 'd']
        sm.overrides = {'b': 'whatever'}

        expected = dedent("""\
        extern _jumptable

        section .code

        global _a
        global _c
        global _d

        _a:
            jmp [_jumptable+0]
        _c:
            jmp [_jumptable+8]
        _d:
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


suite = unittest.TestSuite()
loader = unittest.TestLoader()
suite.addTest(loader.loadTestsFromTestCase(StubMakerInitTest))
suite.addTest(loader.loadTestsFromTestCase(StubMakerGenerateCTest))
suite.addTest(loader.loadTestsFromTestCase(StubMakerGenerateAsmTest))
suite.addTest(loader.loadTestsFromTestCase(StubMakerGenerateMakefileTest))

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)