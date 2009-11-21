
import os
import shutil
import tempfile

from tests.utils.process import spawn
from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase

from tools.utils.io import read, write


class GenerateMapperTest(TestCase):

    def testCreatesComponents(self):
        src = tempfile.mkdtemp()
        write(src, '_exceptions', EXCEPTIONS)
        write(src, '_fill_types', FILL_TYPES)
        write(src, '_numbers_c2py', NUMBERS_C2PY)
        write(src, '_numbers_py2c', NUMBERS_PY2C)
        write(src, '_operator', OPERATOR)
        write(src, '_storedispatch', STOREDISPATCH)

        dst = tempfile.mkdtemp()
        result = spawn('ipy', 'tools/generatemapper.py', src, dst)
        self.assertEquals(result, 0, 'process ended badly')

        def assertFinds(name, expected):
            text = read(dst, '%s.Generated.cs' % name)
            self.assertNotEquals(text.find(expected), -1, 'generated: >>>%s<<<' % text)
        
        assertFinds('PythonMapper_exceptions', EXPECTED_EXCEPTIONS)
        assertFinds('PythonMapper_fill_types', EXPECTED_FILL_TYPES)
        assertFinds('PythonMapper_numbers_c2py', EXPECTED_NUMBERS_C2PY)
        assertFinds('PythonMapper_numbers_py2c', EXPECTED_NUMBERS_PY2C)
        assertFinds('PythonMapper_operator', EXPECTED_OPERATOR)
        assertFinds('PythonMapper_storedispatch', EXPECTED_STOREDISPATCH)

        shutil.rmtree(src)
        shutil.rmtree(dst)

EXCEPTIONS = """
SystemError
OverflowError
"""

EXPECTED_EXCEPTIONS = """
namespace Ironclad
{
    public partial class PythonMapper : PythonApi
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

STOREDISPATCH = """
string
Tuple
Dict
"""

EXPECTED_STOREDISPATCH = """
namespace Ironclad
{
    public partial class PythonMapper : PythonApi
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

EXPECTED_OPERATOR = """
namespace Ironclad
{
    public partial class PythonMapper : PythonApi
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

NUMBERS_C2PY = """

PyInt_FromLong int
PyLong_FromLongLong long (BigInteger)
"""

EXPECTED_NUMBERS_C2PY = """
namespace Ironclad
{
    public partial class PythonMapper : PythonApi
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

NUMBERS_PY2C = """

PyFoo_AsBar MakeSomething double -1.0
PyPing_AsPong MakeSomethingElse pong bat .ToPong()
"""

EXPECTED_NUMBERS_PY2C = """
namespace Ironclad
{
    public partial class PythonMapper : PythonApi
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

EXPECTED_FILL_TYPES = """
namespace Ironclad
{
    public partial class PythonMapper : PythonApi
    {
        public override void
        Fill_PyFoo_Type(IntPtr ptr)
        {
            CPyMarshal.Zero(ptr, Marshal.SizeOf(typeof(PyTypeObject)));
            CPyMarshal.WriteIntField(ptr, typeof(PyTypeObject), "ob_refcnt", 1);
            CPyMarshal.WriteIntField(ptr, typeof(PyTypeObject), "tp_basicsize", Marshal.SizeOf(typeof(PyFooObject)));
            CPyMarshal.WritePtrField(ptr, typeof(PyTypeObject), "tp_init", this.GetFuncPtr("SomeInitMethod"));
            CPyMarshal.WriteIntField(ptr, typeof(PyTypeObject), "tp_itemsize", Marshal.SizeOf(typeof(Byte)));
            CPyMarshal.WritePtrField(ptr, typeof(PyTypeObject), "tp_iter", this.GetFuncPtr("SomeIterMethod"));
            this.map.Associate(ptr, TypeCache.Foo);
        }

        public override void
        Fill_PyBar_Type(IntPtr ptr)
        {
            CPyMarshal.Zero(ptr, Marshal.SizeOf(typeof(PyTypeObject)));
            CPyMarshal.WriteIntField(ptr, typeof(PyTypeObject), "ob_refcnt", 1);
            this.NumberSetupMethod(ptr);
            CPyMarshal.WritePtrField(ptr, typeof(PyTypeObject), "tp_init", this.GetFuncPtr("SomeOtherInitMethod"));
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


suite = makesuite(GenerateMapperTest)
if __name__ == '__main__':
    run(suite)
