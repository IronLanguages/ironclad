import os
import shutil
import tempfile

from System.Diagnostics import Process
from System.Threading import Thread

from textwrap import dedent
from tests.utils.testcase import TestCase

TEMPLATE = dedent("""\
    import sys
    sys.path.insert(0, %r)
    import ironclad
    try:
        %%s
    finally:
        ironclad.shutdown()
    """) % os.path.abspath("build")


def readBinary(filename):
    stream = file(filename, 'rb')
    try:
        return stream.read()
    finally: stream.close()


class FunctionalTestCase(TestCase):
    testDir = None
    removeTestDir = True
    
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
            code = TEMPLATE % code.replace('\n', '\n    ')
        self.write("test.py", code)
        
        process = Process()
        process.StartInfo.FileName = interpreter
        process.StartInfo.Arguments = "test.py"
        process.StartInfo.WorkingDirectory = self.testDir
        process.StartInfo.UseShellExecute = False
        process.StartInfo.RedirectStandardOutput = process.StartInfo.RedirectStandardError = True

        process.Start()
        process.WaitForExit(60000)
        if not process.HasExited:
            process.Kill
        output = process.StandardOutput.ReadToEnd()
        error = process.StandardError.ReadToEnd()
        self.assertEquals(process.ExitCode, 0, "Execution failed: >>>%s<<<\n>>>%s<<<" % (output, error))

        return process.ExitCode, output, error


    def assertRuns(self, code):
        self.runCode(code)
