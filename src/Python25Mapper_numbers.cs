using System;
using System.Runtime.InteropServices;

using Microsoft.Scripting.Math;

using IronPython.Modules;
using IronPython.Runtime;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;

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
        
        public override Py_complex
        PyComplex_AsCComplex(IntPtr objPtr)
        {
            double real = -1.0;
            double imag = 0.0;
            try
            {
                object obj = this.Retrieve(objPtr);
                if (obj == null)
                {
                    throw PythonOps.TypeError("PyComplex_AsCComplex: None cannot be turned into a complex");
                }
                if (obj.GetType() == typeof(Complex64))
                {
                    Complex64 complex = (Complex64)obj;
                    real = complex.Real;
                    imag = complex.Imag;
                }
                else
                {
                    real = this.PyFloat_AsDouble(objPtr);
                }
            }
            catch (Exception e)
            {
                this.LastException = e;
            }
            return new Py_complex(real, imag);
        }
        
        public override IntPtr
        PyComplex_FromDoubles(double real, double imag)
        {
            return this.Store(new Complex64(real, imag));
        }

        public override int
        PyNumber_Check(IntPtr numberPtr)
        {
            object obj = this.Retrieve(numberPtr);
            if (Builtin.isinstance(obj, TypeCache.PythonType))
            {
                return 0;
            }
            if (Builtin.hasattr(this.scratchContext, obj, "__abs__"))
            {
                return 1;
            }
            return 0;
        }

        public override IntPtr
        PyNumber_Int(IntPtr numberPtr)
        {
            try
            {
                return this.Store(PythonCalls.Call(TypeCache.Int32, new object[] {this.Retrieve(numberPtr)}));
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
                // see bugtest.py
                object number = this.Retrieve(numberPtr);
                if (number is string)
                {
                    string str = (string)number;
                    if (str.Trim() == "")
                    {
                        throw PythonOps.ValueError("PyNumber_Long: invalid integer literal");
                    }
                }
                return this.Store(PythonCalls.Call(TypeCache.BigInteger, new object[] {number}));
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
                return this.Store(PythonCalls.Call(TypeCache.Double, new object[] {this.Retrieve(numberPtr)}));
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

        private IntPtr
        Store(Complex64 value)
        {
            IntPtr ptr = this.allocator.Alloc(Marshal.SizeOf(typeof(PyComplexObject)));
            CPyMarshal.WriteIntField(ptr, typeof(PyComplexObject), "ob_refcnt", 1);
            CPyMarshal.WritePtrField(ptr, typeof(PyComplexObject), "ob_type", this.PyComplex_Type);
            CPyMarshal.WriteDoubleField(ptr, typeof(PyComplexObject), "real", value.Real);
            CPyMarshal.WriteDoubleField(ptr, typeof(PyComplexObject), "imag", value.Imag);
            this.map.Associate(ptr, value);
            return ptr;
        }
    }
}
