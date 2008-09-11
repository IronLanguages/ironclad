using System;
using System.Runtime.InteropServices;

using Microsoft.Scripting.Math;

using IronPython.Modules;
using IronPython.Runtime;
using IronPython.Runtime.Operations;

using Ironclad.Structs;

namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        public override IntPtr
        PyBool_FromLong(int value)
        {
            IntPtr ptr = this._Py_ZeroStruct;
            if (value != 0)
            {
                ptr = this._Py_TrueStruct;
            }
            this.IncRef(ptr);
            return ptr;
        }

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

        private IntPtr
        Store(BigInteger value)
        {
            IntPtr ptr = this.allocator.Alloc(Marshal.SizeOf(typeof(PyObject)));
            CPyMarshal.WriteIntField(ptr, typeof(PyObject), "ob_refcnt", 1);
            CPyMarshal.WritePtrField(ptr, typeof(PyObject), "ob_type", this.PyLong_Type);
            this.map.Associate(ptr, value);
            return ptr;
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

        public override IntPtr
        PyNumber_Int(IntPtr numberPtr)
        {
            try
            {
                int result = Converter.ConvertToInt32(this.Retrieve(numberPtr));
                return this.Store(result);
            }
            catch
            {
                return this.PyNumber_Long(numberPtr);
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
        PyNumber_Absolute(IntPtr numberPtr)
        {
            try
            {
                object result = Builtin.abs(this.scratchContext, this.Retrieve(numberPtr));
                return this.Store(result);
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }

        public override IntPtr
        PyNumber_Index(IntPtr numberPtr)
        {
            try
            {
                object result = PythonOperator.index(this.Retrieve(numberPtr));
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
