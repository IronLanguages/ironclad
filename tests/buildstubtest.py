
import os
import shutil
import subprocess
import tempfile
import unittest


def getSymbolNames(path):
    stream = os.popen("pexports %s" % path)
    try:
        return set(stream.readlines())
    finally:
        stream.close()


class BuildStubTest(unittest.TestCase):

    def testBuildStubWithBadParams(self):
        retVal = subprocess.call([
            "python", "buildstub.py"])
        self.assertEquals(retVal, 1, "buildstub didn't bail for 0 param")
        retVal = subprocess.call([
            "python", "buildstub.py", "one"])
        self.assertEquals(retVal, 1, "buildstub didn't bail for 1 param")
        retVal = subprocess.call([
            "python", "buildstub.py", "one", "two", "three", "four"])
        self.assertEquals(retVal, 1, "buildstub didn't bail for 4 param")


    def testBuildStubCreatesOutputDll(self):
        inputPath = "tests\\data\\exportsymbols.dll"
        tempDir = tempfile.gettempdir()
        ourTempDir = os.path.join(tempDir, 'buildstubtest')
        if os.path.exists(ourTempDir):
            shutil.rmtree(ourTempDir)
        retVal = subprocess.call([
            "python", "buildstub.py", inputPath, ourTempDir])
        self.assertEquals(retVal, 0, "process ended badly")
        outputPath = os.path.join(ourTempDir, "exportsymbols.dll")
        self.assertTrue(os.path.exists(outputPath))

        inputLines = getSymbolNames(inputPath)
        outputLines = getSymbolNames(outputPath)

        inputLines |= set(["init\n", "jumptable DATA\n"])
        self.assertEquals(outputLines, inputLines, "bad output symbols")



suite = unittest.TestSuite()
loader = unittest.TestLoader()
suite.addTest(loader.loadTestsFromTestCase(BuildStubTest))

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)