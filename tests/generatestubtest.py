
from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase

from textwrap import dedent

from tools.utils.stubgen import StubGenerator


class StubGeneratorTest(TestCase):

    def testRun(self):
        gen = StubGenerator()
        output = gen.run(INPUTS)
        self.assertEquals(output, EXPECT_OUTPUT)


INPUTS = {
    'PURE_C_SYMBOLS': set('FUNC1 DATA1 DATA2'.split()),
    'EXPORTED_FUNCTIONS': 'FUNC1 FUNC2'.split(),
    'EXTRA_FUNCTIONS': ['void FUNC3(void);', 'int FUNC4(void);'],
    'MGD_API_DATA': 'DATA3 DATA2'.split()
}

EXPECT_STUBINIT = """\
void *jumptable[3];

typedef void *(*getfuncptr_fp)(const char*);
typedef void (*registerdata_fp)(const char*, const void*);
void init(getfuncptr_fp getfuncptr, registerdata_fp registerdata)
{
    registerdata("DATA3", &DATA3);
    registerdata("DATA2", &DATA2);
    jumptable[0] = getfuncptr("FUNC2");
    jumptable[1] = getfuncptr("FUNC3");
    jumptable[2] = getfuncptr("FUNC4");
}
"""

EXPECT_JUMPS = """\
default rel
bits 64

extern jumptable

section .code

global FUNC2
global FUNC3
global FUNC4
FUNC2:
    jmp [jumptable+0]
FUNC3:
    jmp [jumptable+8]
FUNC4:
    jmp [jumptable+16]
"""

EXPECT_HEADER = """\
void FUNC3(void);
int FUNC4(void);
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
