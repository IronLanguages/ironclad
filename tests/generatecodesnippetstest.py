
import os
import shutil
import sys
import tempfile

from tests.utils.process import spawn
from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase

from tools.utils.io import read, write


class GenerateCodeSnippetsTest(TestCase):

    def testCreatesComponents(self):
        src = tempfile.mkdtemp()
        for (name, contents) in SNIPPETS_FILES.items():
            write(src, name, contents)

        dst = tempfile.mkdtemp()
        exe = ('dotnet', sys.executable) if sys.executable.endswith('.dll') else (sys.executable,)
        result = spawn(*exe, "tools/generatecodesnippets.py", src, dst)
        self.assertEqual(result, 0, "process ended badly")

        def assertFinds(name, expected):
            text = read(dst, '%s.Generated.cs' % name)
            self.assertNotEqual(text.find(expected), -1, "generated: >>>%s<<<" % text)
        
        assertFinds('CodeSnippets', EXPECTED_SNIPPETS)

        shutil.rmtree(src)
        shutil.rmtree(dst)


SNIPPETS_FILES = {
    'FOO.py': 'some random pile of code',
    'BAR.py': 'some random pile of code, with "double" quotes',
}

EXPECTED_SNIPPETS = """
namespace Ironclad
{
    internal class CodeSnippets
    {
        public const string BAR = @"some random pile of code, with ""double"" quotes";

        public const string FOO = @"some random pile of code";
    }
}
"""


suite = makesuite(GenerateCodeSnippetsTest)
if __name__ == '__main__':
    run(suite)
