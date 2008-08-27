
import os
import shutil
import tempfile

from tests.utils.process import spawn
from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase

from tools.stubmaker import popen

def GetPexportsLines(path):
    stream = popen("pexports", path.replace('/cygdrive/c', 'c:'))
    try:
        return set(map(lambda s: s.strip(), stream.readlines()))
    finally:
        stream.close()


class BuildStubTest(TestCase):

    def testBuildStubWithBadParams(self):
        retVal = spawn("ipy", "tools/buildstub.py")
        self.assertEquals(retVal, 1, "buildstub didn't bail for 0 param")
        retVal = spawn("ipy", "tools/buildstub.py", "one")
        self.assertEquals(retVal, 1, "buildstub didn't bail for 1 param")
        retVal = spawn("ipy", "tools/buildstub.py", "one", "two", "three", "four")
        self.assertEquals(retVal, 1, "buildstub didn't bail for 4 param")


    def testBuildStubCreatesOutputFiles(self):
        inputPath = "tests/data/exportsymbols.dll"
        overridePath = "tests/data/stub"
        tempDir = tempfile.mkdtemp()
        ourTempDir = os.path.join(tempDir, 'buildstubtest')

        def testGenerates(*extraArgs):
            if os.path.exists(ourTempDir):
                shutil.rmtree(ourTempDir)

            retVal = spawn("ipy", "tools/buildstub.py", *extraArgs)
            self.assertEquals(retVal, 0, "process ended badly")
            cPath = os.path.join(ourTempDir, "stub.generated.c")
            self.assertTrue(os.path.exists(cPath))
            asmPath = os.path.join(ourTempDir, "stub.generated.asm")
            self.assertTrue(os.path.exists(asmPath))

        testGenerates(inputPath, ourTempDir)
        testGenerates(inputPath, ourTempDir, overridePath)
        shutil.rmtree(tempDir)


class Python25StubTest(TestCase):

    def testPython25Stub(self):
        f = open("tests/data/python25-pexports")
        try:
            python25exports = set(map(lambda s: s.strip(), f.readlines()))
        finally:
            f.close()

        python25exports |= set(["init", "jumptable DATA"])
        generatedExports = GetPexportsLines("build/python25.dll")

        self.assertEquals(generatedExports.issuperset(python25exports), True,
                          "build product wrong")

suite = makesuite(BuildStubTest, Python25StubTest)

if __name__ == '__main__':
    run(suite)
