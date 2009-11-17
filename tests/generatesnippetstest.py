
import os
import shutil
import tempfile

from tests.utils.process import spawn
from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase

from tools.utils.file import read, write


class GenerateMapperTest(TestCase):

    def testCreatesComponents(self):
        src = tempfile.mkdtemp()
        for (name, contents) in SNIPPETS_FILES.items():
            write(src, name, contents)

        dst = tempfile.mkdtemp()
        result = spawn("ipy", "tools/generatesnippets.py", src, dst)
        self.assertEquals(result, 0, "process ended badly")

        def assertFinds(name, expected):
            text = read(dst, '%s.Generated.cs' % name)
            self.assertNotEquals(text.find(expected), -1, "generated: >>>%s<<<" % text)
        
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


suite = makesuite(GenerateMapperTest)
if __name__ == '__main__':
    run(suite)
