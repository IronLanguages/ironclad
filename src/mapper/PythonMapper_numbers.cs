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
    public partial class PythonMapper : PythonApi
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
            Py_complex result = new Py_complex();
            result.real = real;
            result.imag = imag;
            return result;
        }
        
        public override IntPtr
        PyComplex_FromDoubles(double real, double imag)
        {
            return this.Store(new Complex64(real, imag));
        }
        
        public override uint
        PyInt_AsUnsignedLongMask(IntPtr valuePtr)
        {
            try
            {
                BigInteger unmasked = this.MakeBigInteger(this.Retrieve(valuePtr));
                BigInteger mask = new BigInteger(UInt32.MaxValue) + 1;
                BigInteger masked = BigInteger.Mod(unmasked, mask);
                if (masked < 0)
                {
                    masked += mask;
                }
                return masked.ToUInt32();
            }
            catch (Exception e)
            {
                this.LastException = e;
                return 0xFFFFFFFF;
            }
        }
        
        public override int
        _PyLong_Sign(IntPtr valuePtr)
        {
            BigInteger value = this.MakeBigInteger(this.Retrieve(valuePtr));
            if (value > 0)
            {
                return 1;
            }
            else if (value < 0)
            {
                return -1;
            }
            return 0;
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
                object result = PythonCalls.Call(TypeCache.Int32, new object[] {this.Retrieve(numberPtr)});
                if (!(result is Int32))
                {
                    result = Converter.ConvertToBigInteger(result);
                }
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
                object number = this.Retrieve(numberPtr);
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

        public override IntPtr
        IC_PyFloat_New(IntPtr typePtr, IntPtr argsPtr, IntPtr kwargsPtr)
        {
            try
            {
                PythonTuple args = (PythonTuple) this.Retrieve(argsPtr);
                return this.Store(PythonCalls.Call(this.scratchContext, TypeCache.Double, new object[] {args[0]}));
            }
            catch(Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }

        public override IntPtr
        IC_PyInt_New(IntPtr typePtr, IntPtr argsPtr, IntPtr kwargsPtr)
        {
            try
            {
                PythonTuple args = (PythonTuple) this.Retrieve(argsPtr);
                return this.Store(PythonCalls.Call(this.scratchContext, TypeCache.Int32, new object[] {args[0]}));
            }
            catch(Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }

        private IntPtr
        StoreTyped(bool value)
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
        StoreTyped(int value)
        {
            IntPtr ptr = this.allocator.Alloc((uint)Marshal.SizeOf(typeof(PyIntObject)));
            CPyMarshal.WriteIntField(ptr, typeof(PyIntObject), "ob_refcnt", 1);
            CPyMarshal.WritePtrField(ptr, typeof(PyIntObject), "ob_type", this.PyInt_Type);
            CPyMarshal.WriteIntField(ptr, typeof(PyIntObject), "ob_ival", value);
            this.map.Associate(ptr, value);
            return ptr;
        }

        private IntPtr
        StoreTyped(uint value)
        {
            if (value <= Int32.MaxValue)
            {
                return this.Store((int)value);
            }
            return this.Store(this.MakeBigInteger(value));
        }

        private IntPtr
        StoreTyped(BigInteger value)
        {
            IntPtr ptr = this.allocator.Alloc((uint)Marshal.SizeOf(typeof(PyObject)));
            CPyMarshal.WriteIntField(ptr, typeof(PyObject), "ob_refcnt", 1);
            CPyMarshal.WritePtrField(ptr, typeof(PyObject), "ob_type", this.PyLong_Type);
            this.map.Associate(ptr, value);
            return ptr;
        }

        private IntPtr
        StoreTyped(double value)
        {
            IntPtr ptr = this.allocator.Alloc((uint)Marshal.SizeOf(typeof(PyFloatObject)));
            CPyMarshal.WriteIntField(ptr, typeof(PyFloatObject), "ob_refcnt", 1);
            CPyMarshal.WritePtrField(ptr, typeof(PyFloatObject), "ob_type", this.PyFloat_Type);
            CPyMarshal.WriteDoubleField(ptr, typeof(PyFloatObject), "ob_fval", value);
            this.map.Associate(ptr, value);
            return ptr;
        }

        private IntPtr
        StoreTyped(Complex64 value)
        {
            IntPtr ptr = this.allocator.Alloc((uint)Marshal.SizeOf(typeof(PyComplexObject)));
            CPyMarshal.WriteIntField(ptr, typeof(PyComplexObject), "ob_refcnt", 1);
            CPyMarshal.WritePtrField(ptr, typeof(PyComplexObject), "ob_type", this.PyComplex_Type);
            IntPtr cpxptr = CPyMarshal.GetField(ptr, typeof(PyComplexObject), "cval");
            CPyMarshal.WriteDoubleField(cpxptr, typeof(Py_complex), "real", value.Real);
            CPyMarshal.WriteDoubleField(cpxptr, typeof(Py_complex), "imag", value.Imag);
            this.map.Associate(ptr, value);
            return ptr;
        }
    }
}
