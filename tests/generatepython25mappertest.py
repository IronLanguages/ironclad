
import os
import shutil
import tempfile
from tests.utils.process import spawn
from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase

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


class GeneratePython25MapperTest(TestCase):

    def testCreatesPython25MapperComponents(self):
        tempDir = tempfile.mkdtemp()
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
        shutil.rmtree(tempDir)

EXCEPTIONS = """
SystemError
OverflowError
"""

EXPECTED_EXCEPTIONS = """
using System;
using IronPython.Runtime;
using IronPython.Runtime.Exceptions;
using IronPython.Runtime.Types;
using Microsoft.Scripting.Math;

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
using Microsoft.Scripting.Math;

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
using Microsoft.Scripting.Math;

namespace Ironclad
{
    public partial class Python25Mapper : PythonMapper
    {
        private IntPtr StoreDispatch(object obj)
        {
            if (obj.GetType() == typeof(string)) { return this.Store((string)obj); }
            if (obj.GetType() == typeof(Tuple)) { return this.Store((Tuple)obj); }
            if (obj.GetType() == typeof(Dict)) { return this.Store((Dict)obj); }
            return this.StoreObject(obj);
        }
    }
}
"""

suite = makesuite(GeneratePython25MapperTest)

if __name__ == '__main__':
    run(suite)