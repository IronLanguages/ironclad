using System;
using System.Runtime.InteropServices;

using Microsoft.Scripting.Math;

using IronPython.Runtime;
using IronPython.Runtime.Calls;
using IronPython.Runtime.Operations;

using Ironclad.Structs;

namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        private IntPtr
        Store(bool value)
        {
            IntPtr ptr = this._Py_ZeroStruct;
            if (value)
            {
                ptr = this._Py_TrueStruct;
            }
            this.IncRef(ptr);
            return ptr;
        }

        public override IntPtr
        PyNumber_Add(IntPtr arg1ptr, IntPtr arg2ptr)
        {
            try
            {
                object result = PythonSites.Add(this.Retrieve(arg1ptr), this.Retrieve(arg2ptr));
                return this.Store(result);
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }


        public override IntPtr
        PyNumber_Subtract(IntPtr arg1ptr, IntPtr arg2ptr)
        {
            try
            {
                object result = PythonSites.Subtract(this.Retrieve(arg1ptr), this.Retrieve(arg2ptr));
                return this.Store(result);
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }


        public override IntPtr
        PyNumber_Multiply(IntPtr arg1ptr, IntPtr arg2ptr)
        {
            try
            {
                object result = PythonSites.Multiply(this.Retrieve(arg1ptr), this.Retrieve(arg2ptr));
                return this.Store(result);
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }


        public override IntPtr
        PyNumber_Divide(IntPtr arg1ptr, IntPtr arg2ptr)
        {
            try
            {
                object result = PythonSites.Divide(this.Retrieve(arg1ptr), this.Retrieve(arg2ptr));
                return this.Store(result);
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }


        public override IntPtr
        PyNumber_Absolute(IntPtr numberPtr)
        {
            try
            {
                object result = Builtin.abs(DefaultContext.Default, this.Retrieve(numberPtr));
                return this.Store(result);
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }


        public override IntPtr
        PyNumber_Long(IntPtr numberPtr)
        {
            try
            {
                BigInteger result = Converter.ConvertToBigInteger(this.Retrieve(numberPtr));
                return this.Store(result);
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }
        
        
        public override IntPtr
        PyNumber_Float(IntPtr numberPtr)
        {
            try
            {
                double result = Converter.ConvertToDouble(this.Retrieve(numberPtr));
                return this.Store(result);
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }


        public override IntPtr
        PyInt_FromLong(int value)
        {
            IntPtr result = this.Store(value);
            return result;
        }
        
        
        public override IntPtr
        PyInt_FromSsize_t(int value)
        {
            IntPtr result = this.Store(value);
            return result;
        }


        public override int
        PyInt_AsLong(IntPtr valuePtr)
        {
            int result = Converter.ConvertToInt32(this.Retrieve(valuePtr));
            return result;
        }

        private IntPtr
        Store(int value)
        {
            IntPtr ptr = this.allocator.Alloc(Marshal.SizeOf(typeof(PyIntObject)));
            CPyMarshal.WriteIntField(ptr, typeof(PyIntObject), "ob_refcnt", 1);
            CPyMarshal.WritePtrField(ptr, typeof(PyIntObject), "ob_type", this.PyInt_Type);
            CPyMarshal.WriteIntField(ptr, typeof(PyIntObject), "ob_ival", value);
            this.map.Associate(ptr, value);
            return ptr;
        }


        public override int
        PyLong_AsLong(IntPtr valuePtr)
        {
            try
            {
                BigInteger value = Converter.ConvertToBigInteger(this.Retrieve(valuePtr));
                return value.ToInt32();
            }
            catch (Exception e)
            {
                this.LastException = e;
                return 0;
            }
        }


        public override Int64
        PyLong_AsLongLong(IntPtr valuePtr)
        {
            try
            {
                BigInteger value = Converter.ConvertToBigInteger(this.Retrieve(valuePtr));
                return value.ToInt64();
            }
            catch (Exception e)
            {
                this.LastException = e;
                return 0;
            }
        }

        public override IntPtr
        PyLong_FromLongLong(long value)
        {
            IntPtr result = this.Store((BigInteger)value);
            return result;
        }

        public override IntPtr
        PyLong_FromUnsignedLong(uint value)
        {
            IntPtr result = this.Store((BigInteger)value);
            return result;
        }


        public override IntPtr
        PyLong_FromUnsignedLongLong(ulong value)
        {
            IntPtr result = this.Store((BigInteger)value);
            return result;
        }

        private IntPtr
        Store(BigInteger value)
        {
            IntPtr ptr = this.allocator.Alloc(Marshal.SizeOf(typeof(PyObject)));
            CPyMarshal.WriteIntField(ptr, typeof(PyObject), "ob_refcnt", 1);
            CPyMarshal.WritePtrField(ptr, typeof(PyObject), "ob_type", this.PyLong_Type);
            this.map.Associate(ptr, value);
            return ptr;
        }
        
        public override IntPtr
        PyFloat_FromDouble(double value)
        {
            return this.Store(value);
        }
        
        public override double
        PyFloat_AsDouble(IntPtr numberPtr)
        {
            try
            {
                return Converter.ConvertToDouble(this.Retrieve(numberPtr));
            }
            catch (Exception e)
            {
                this.LastException = e;
                return -1.0;
            }
        }

        private IntPtr
        Store(double value)
        {
            IntPtr ptr = this.allocator.Alloc(Marshal.SizeOf(typeof(PyFloatObject)));
            CPyMarshal.WriteIntField(ptr, typeof(PyFloatObject), "ob_refcnt", 1);
            CPyMarshal.WritePtrField(ptr, typeof(PyFloatObject), "ob_type", this.PyFloat_Type);
            CPyMarshal.WriteDoubleField(ptr, typeof(PyFloatObject), "ob_fval", value);
            this.map.Associate(ptr, value);
            return ptr;
        }
        
    }

}
