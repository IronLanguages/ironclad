
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
            write("store_dispatch", STORE)
            write("operator", OPERATOR)
            write("numbers_convert_c2py", NUMBERS_CONVERT_C2PY)
            write("numbers_convert_py2c", NUMBERS_CONVERT_PY2C)
            write("fill_types", FILL_TYPES)

            retVal = spawn("ipy", toolPath, testSrcDir, testBuildDir)
            self.assertEquals(retVal, 0, "process ended badly")

            os.chdir(testBuildDir)
            self.assertEquals(read("Python25Mapper_exceptions.Generated.cs"), EXPECTED_EXCEPTIONS)
            self.assertEquals(read("Python25Mapper_store_dispatch.Generated.cs"), EXPECTED_STORE)
            self.assertEquals(read("Python25Mapper_operator.Generated.cs"), EXPECTED_OPERATOR)
            self.assertEquals(read("Python25Mapper_numbers_convert_c2py.Generated.cs"), EXPECTED_NUMBERS_CONVERT_C2PY)
            self.assertEquals(read("Python25Mapper_numbers_convert_py2c.Generated.cs"), EXPECTED_NUMBERS_CONVERT_PY2C)
            self.assertEquals(read("Python25Mapper_fill_types.Generated.cs"), EXPECTED_FILL_TYPES)

        finally:
            os.chdir(origCwd)
        shutil.rmtree(tempDir)

USINGS = """\
/* This file was generated by tools/generatepython25mapper.py */
using System;
using System.Collections;
using System.Runtime.InteropServices;
using IronPython.Modules;
using IronPython.Runtime;
using IronPython.Runtime.Exceptions;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;
using Microsoft.Scripting.Math;
using Ironclad.Structs;
"""

EXCEPTIONS = """
SystemError
OverflowError
"""

EXPECTED_EXCEPTIONS = USINGS + """
namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        public override void Fill_PyExc_SystemError(IntPtr addr)
        {
            IntPtr value = this.Store(PythonExceptions.SystemError);
            CPyMarshal.WritePtr(addr, value);
        }

        public override void Fill_PyExc_OverflowError(IntPtr addr)
        {
            IntPtr value = this.Store(PythonExceptions.OverflowError);
            CPyMarshal.WritePtr(addr, value);
        }
    }
}
"""

STORE = """
string
Tuple
Dict
"""

EXPECTED_STORE = USINGS + """
namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        private IntPtr StoreDispatch(object obj)
        {
            if (obj is string) { return this.StoreTyped((string)obj); }
            if (obj is Tuple) { return this.StoreTyped((Tuple)obj); }
            if (obj is Dict) { return this.StoreTyped((Dict)obj); }
            return this.StoreObject(obj);
        }
    }
}
"""

OPERATOR = """
PyNumber_Add add
PyNumber_Remainder mod
"""

EXPECTED_OPERATOR = USINGS + """
namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        public override IntPtr
        PyNumber_Add(IntPtr arg1ptr, IntPtr arg2ptr)
        {
            try
            {
                object result = PythonOperator.add(this.scratchContext, this.Retrieve(arg1ptr), this.Retrieve(arg2ptr));
                return this.Store(result);
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }

        public override IntPtr
        PyNumber_Remainder(IntPtr arg1ptr, IntPtr arg2ptr)
        {
            try
            {
                object result = PythonOperator.mod(this.scratchContext, this.Retrieve(arg1ptr), this.Retrieve(arg2ptr));
                return this.Store(result);
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }
    }
}
"""

NUMBERS_CONVERT_C2PY = """

PyInt_FromLong int
PyLong_FromLongLong long (BigInteger)
"""

EXPECTED_NUMBERS_CONVERT_C2PY = USINGS + """
namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        public override IntPtr
        PyInt_FromLong(int value)
        {
            return this.Store(value);
        }

        public override IntPtr
        PyLong_FromLongLong(long value)
        {
            return this.Store((BigInteger)value);
        }
    }
}
"""

NUMBERS_CONVERT_PY2C = """

PyFoo_AsBar MakeSomething double -1.0
PyPing_AsPong MakeSomethingElse pong bat .ToPong()
"""

EXPECTED_NUMBERS_CONVERT_PY2C = USINGS + """
namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        public override double
        PyFoo_AsBar(IntPtr valuePtr)
        {
            try
            {
                return this.MakeSomething(this.Retrieve(valuePtr));
            }
            catch (Exception e)
            {
                this.LastException = e;
                return -1.0;
            }
        }

        public override pong
        PyPing_AsPong(IntPtr valuePtr)
        {
            try
            {
                return this.MakeSomethingElse(this.Retrieve(valuePtr)).ToPong();
            }
            catch (Exception e)
            {
                this.LastException = e;
                return bat;
            }
        }
    }
}
"""

FILL_TYPES = """

PyFoo_Type TypeCache.Foo {"tp_init": "SomeInitMethod", "tp_iter": "SomeIterMethod", "tp_basicsize": "PyFooObject", "tp_itemsize": "Byte"}
PyBar_Type TypeCache.Bar {"tp_init": "SomeOtherInitMethod", "tp_as_number": "NumberSetupMethod"}
PyBaz_Type TypeCache.Baz
"""

EXPECTED_FILL_TYPES = USINGS + """
namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        public override void
        Fill_PyFoo_Type(IntPtr ptr)
        {
            CPyMarshal.Zero(ptr, Marshal.SizeOf(typeof(PyTypeObject)));
            CPyMarshal.WriteIntField(ptr, typeof(PyTypeObject), "ob_refcnt", 1);
            CPyMarshal.WriteIntField(ptr, typeof(PyTypeObject), "tp_basicsize", Marshal.SizeOf(typeof(PyFooObject)));
            CPyMarshal.WritePtrField(ptr, typeof(PyTypeObject), "tp_init", this.GetAddress("SomeInitMethod"));
            CPyMarshal.WriteIntField(ptr, typeof(PyTypeObject), "tp_itemsize", Marshal.SizeOf(typeof(Byte)));
            CPyMarshal.WritePtrField(ptr, typeof(PyTypeObject), "tp_iter", this.GetAddress("SomeIterMethod"));
            this.map.Associate(ptr, TypeCache.Foo);
        }

        public override void
        Fill_PyBar_Type(IntPtr ptr)
        {
            CPyMarshal.Zero(ptr, Marshal.SizeOf(typeof(PyTypeObject)));
            CPyMarshal.WriteIntField(ptr, typeof(PyTypeObject), "ob_refcnt", 1);
            this.NumberSetupMethod(ptr);
            CPyMarshal.WritePtrField(ptr, typeof(PyTypeObject), "tp_init", this.GetAddress("SomeOtherInitMethod"));
            this.map.Associate(ptr, TypeCache.Bar);
        }

        public override void
        Fill_PyBaz_Type(IntPtr ptr)
        {
            CPyMarshal.Zero(ptr, Marshal.SizeOf(typeof(PyTypeObject)));
            CPyMarshal.WriteIntField(ptr, typeof(PyTypeObject), "ob_refcnt", 1);

            this.map.Associate(ptr, TypeCache.Baz);
        }
    }
}
"""

suite = makesuite(GeneratePython25MapperTest)

if __name__ == '__main__':
    run(suite)
