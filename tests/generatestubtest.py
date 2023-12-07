
from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase

from textwrap import dedent

from tools.utils.stubgen import StubGenerator


class StubGeneratorTest(TestCase):

    def testRun(self):
        gen = StubGenerator()
        output = gen.run(INPUTS)
        self.assertEqual(output, EXPECT_OUTPUT)


INPUTS = {
    'PURE_C_SYMBOLS': set('FUNC1 FUNCEX FUNCNEX DATA1 DATA2'.split()),
    'EXPORTED_FUNCTIONS': 'FUNC1 FUNC2 FUNCEX'.split(),
    'EXPORTED_DATA': 'DATA2 DATA3'.split(),
    'EXTRA_FUNCTIONS': ['void FUNC3(void);', 'int FUNC4(void);', 'binaryfunc OPER;'],
    'MGD_API_DATA': 'FUNCEX FUNCNEX DATA3 DATA2 DATA4'.split()
}

EXPECT_STUBINIT = """\
#ifdef _MSC_VER
    #define DLLEXPORT __declspec(dllexport)
#else
    #define DLLEXPORT
#endif

void *jumptable[4];
extern void *jumptable_addr;

typedef void *(*getfuncptr_fp)(const char*);
typedef void (*registerdata_fp)(const char*, const void*);
DLLEXPORT void init(getfuncptr_fp getfuncptr, registerdata_fp registerdata)
{
    jumptable_addr = jumptable;
    registerdata("FUNCEX", &FUNCEX);
    registerdata("DATA3", &DATA3);
    registerdata("DATA2", &DATA2);
    jumptable[0] = getfuncptr("FUNC2");
    jumptable[1] = getfuncptr("FUNC3");
    jumptable[2] = getfuncptr("FUNC4");
    jumptable[3] = getfuncptr("OPER");
}
"""

EXPECT_JUMPS = """\
default rel
bits 64

section .bss

global jumptable_addr
jumptable_addr resq 1

section .text

global FUNC2
global FUNC3
global FUNC4
global OPER

    nop
    nop
FUNC2:
    jmp [jumptable_addr+0]
FUNC3:
    jmp [jumptable_addr+8]
FUNC4:
    jmp [jumptable_addr+16]
OPER:
    jmp [jumptable_addr+24]
"""

EXPECT_HEADER = """\
extern void FUNC3(void);
extern int FUNC4(void);
extern binaryfunc OPER;
"""

EXPECT_OUTPUT = {
    'STUBINIT': EXPECT_STUBINIT,
    'HEADER': EXPECT_HEADER,
    'JUMPS': EXPECT_JUMPS,
}

suite = makesuite(
    StubGeneratorTest,
)

if __name__ == '__main__':
    run(suite)
