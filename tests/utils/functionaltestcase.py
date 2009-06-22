import os
import shutil
import tempfile

from System.Diagnostics import Process
from System.Threading import Thread

from textwrap import dedent
from tests.utils.testcase import TestCase


def readBinary(filename):
    stream = file(filename, 'rb')
    try:
        return stream.read()
    finally:
        stream.close()


class FunctionalTestCase(TestCase):
    testDir = None
    removeTestDir = True

    TEMPLATE = dedent("""\
        import sys
        sys.path.insert(0, %r)
        import ironclad
        %%s
        """) % os.path.abspath("build")
    
    def setUp(self):
        TestCase.setUp(self)
        if not self.testDir:
            self.testDir = tempfile.mkdtemp()
        if not os.path.exists(self.testDir):
            os.makedirs(self.testDir)
        

    def tearDown(self):
        TestCase.tearDown(self)
        if self.removeTestDir:
            shutil.rmtree(self.testDir)


    def write(self, name, code):
        testFile = open(os.path.join(self.testDir, name), 'w')
        try:
            testFile.write(code)
        finally:
            testFile.close()


    def runCode(self, code, interpreter="ipy.exe"):
        if interpreter == "ipy.exe":
            code = self.TEMPLATE % code
        self.write("test-code.py", code)
        
        process = Process()
        process.StartInfo.FileName = interpreter
        process.StartInfo.Arguments = "test-code.py"
        process.StartInfo.WorkingDirectory = self.testDir
        process.StartInfo.UseShellExecute = False
        process.StartInfo.RedirectStandardOutput = process.StartInfo.RedirectStandardError = True

        process.Start()
        process.WaitForExit(600000)
        if not process.HasExited:
            process.Kill()
        output = process.StandardOutput.ReadToEnd()
        error = process.StandardError.ReadToEnd()

        return process.ExitCode, output, error


    def assertRuns(self, code):
        exit_code, output, error = self.runCode(code)
        self.assertEquals(exit_code, 0, "Execution failed: >>>%s<<<\n>>>%s<<<" % (output, error))
