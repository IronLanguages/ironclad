
import os
import shutil
import tempfile

from tests.utils.process import spawn
from tests.utils.runtest import automakesuite, run
from tests.utils.testcase import TestCase

from tools.utils import popen, read_interesting_lines

def GetPexportsLines(path):
    stream = popen("pexports", path.replace('/cygdrive/c', 'c:'))
    try:
        return set(map(lambda s: s.strip(), stream.readlines()))
    finally:
        stream.close()


class GenerateStubTest(TestCase):

    def testGenerateStubCreatesOutputFiles(self):
        src_dll = 'tests/data/exportsymbols.dll'
        src = 'tests/data/stub'
        
        tmp = tempfile.mkdtemp()
        dst = os.path.join(tmp, 'stub'); os.mkdir(dst)
        dst_include = os.path.join(dst, 'Include'); os.mkdir(dst_include)

        result = spawn('ipy', 'tools/generatestub.py', src_dll, src, dst)
        self.assertEquals(result, 0, 'process ended badly')
        
        def assertExists(dir_, name):
            self.assertTrue(os.path.exists(os.path.join(dir_, name)))
        assertExists(dst, 'stubinit.generated.c')
        assertExists(dst, 'jumps.generated.asm')
        assertExists(dst_include, '_mgd_function_prototypes.generated.h')

        shutil.rmtree(tmp)

class PythonStubTest(TestCase):

    def testPythonStub(self):
        path = os.path.join('tests', 'data', 'python26-pexports')
        python26exports = set(read_interesting_lines(path))
        generatedExports = GetPexportsLines("build/ironclad/python26.dll")
        self.assertEquals(python26exports - generatedExports, set())

suite = automakesuite(locals())
if __name__ == '__main__':
    run(suite)
