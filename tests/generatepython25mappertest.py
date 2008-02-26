
import os
import shutil
import tempfile
import unittest
from tests.utils.process import spawn
from tests.utils.runtest import makesuite, run

def write(name, text):
    f = open(name, 'w')
    try:
        f.write(text)
    finally:
        f.close()



class GeneratePython25MapperTest(unittest.TestCase):

    def testCreatesPython25Mapper_Exceptions_cs(self):
        tempDir = tempfile.gettempdir()
        testBuildDir = os.path.join(tempDir, 'generatepython25mappertest')
        if os.path.exists(testBuildDir):
            shutil.rmtree(testBuildDir)
        os.mkdir(testBuildDir)
        testSrcDir = os.path.join(testBuildDir, 'python25mapper_components')
        os.mkdir(testSrcDir)

        origCwd = os.getcwd()
        toolPath = os.path.join(origCwd, "tools/generatepython25mapper.py")

        os.chdir(testSrcDir)
        try:
            write("exceptions", EXCEPTIONS)

            retVal = spawn("ipy", toolPath)
            self.assertEquals(retVal, 0, "process ended badly")

            os.chdir(testBuildDir)
            f = open("Python25Mapper_exceptions.cs", 'r')
            try:
                result = f.read()
                self.assertEquals(result, EXPECTED_OUTPUT, "generated wrong")
            finally:
                f.close()

        finally:
            os.chdir(origCwd)

EXCEPTIONS = """
SystemError
OverflowError
"""


EXPECTED_OUTPUT = """
using System;

using IronPython.Runtime.Exceptions;

namespace Ironclad
{
    public partial class Python25Mapper : PythonMapper
    {
        public override IntPtr Make_PyExc_SystemError()
        {
            return this.Store(ExceptionConverter.GetPythonException("SystemError"));
        }

        public override IntPtr Make_PyExc_OverflowError()
        {
            return this.Store(ExceptionConverter.GetPythonException("OverflowError"));
        }
    }
}
"""


suite = makesuite(GeneratePython25MapperTest)

if __name__ == '__main__':
    run(suite)