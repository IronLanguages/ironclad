
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

def read(name):
    f = open(name)
    try:
        return f.read()
    finally:
        f.close()


class GeneratePython25MapperTest(unittest.TestCase):

    def testCreatesPython25MapperComponents(self):
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
            write("builtin_exceptions", BUILTIN_EXCEPTIONS)
            write("store", STORE)

            retVal = spawn("ipy", toolPath)
            self.assertEquals(retVal, 0, "process ended badly")

            os.chdir(testBuildDir)
            self.assertEquals(read("Python25Mapper_exceptions.cs"), EXPECTED_EXCEPTIONS, 
                              "generated exceptions wrong")
            self.assertEquals(read("Python25Mapper_builtin_exceptions.cs"), EXPECTED_BUILTIN_EXCEPTIONS, 
                              "generated builtin exceptions wrong")
            self.assertEquals(read("Python25Mapper_store.cs"), EXPECTED_STORE, 
                              "generated wrong")

        finally:
            os.chdir(origCwd)

EXCEPTIONS = """
SystemError
OverflowError
"""

EXPECTED_EXCEPTIONS = """
using System;
using IronPython.Runtime;
using IronPython.Runtime.Exceptions;
using IronPython.Runtime.Types;

namespace Ironclad
{
    public partial class Python25Mapper : PythonMapper
    {
        public override IntPtr Make_PyExc_SystemError()
        {
            return this.Store(PythonExceptions.SystemError);
        }

        public override IntPtr Make_PyExc_OverflowError()
        {
            return this.Store(PythonExceptions.OverflowError);
        }
    }
}
"""

BUILTIN_EXCEPTIONS = """
BaseException
WindowsError
"""

EXPECTED_BUILTIN_EXCEPTIONS = """
using System;
using IronPython.Runtime;
using IronPython.Runtime.Exceptions;
using IronPython.Runtime.Types;

namespace Ironclad
{
    public partial class Python25Mapper : PythonMapper
    {
        public override IntPtr Make_PyExc_BaseException()
        {
            return this.Store(Builtin.BaseException);
        }

        public override IntPtr Make_PyExc_WindowsError()
        {
            return this.Store(Builtin.WindowsError);
        }
    }
}
"""

STORE = """
string
Tuple
Dict
"""

EXPECTED_STORE = """
using System;
using IronPython.Runtime;
using IronPython.Runtime.Exceptions;
using IronPython.Runtime.Types;

namespace Ironclad
{
    public partial class Python25Mapper : PythonMapper
    {
        private IntPtr StoreDispatch(object obj)
        {
            string attempt0 = obj as string;
            if (attempt0 != null) { return this.Store(attempt0); }
            Tuple attempt1 = obj as Tuple;
            if (attempt1 != null) { return this.Store(attempt1); }
            Dict attempt2 = obj as Dict;
            if (attempt2 != null) { return this.Store(attempt2); }
            return this.StoreObject(obj);
        }
    }
}
"""

suite = makesuite(GeneratePython25MapperTest)

if __name__ == '__main__':
    run(suite)