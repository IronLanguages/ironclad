using System;
using System.Runtime.InteropServices;

using Microsoft.Scripting.Math;

using Ironclad.Structs;

namespace Ironclad
{
    public partial class Python25Mapper : PythonMapper
    {
        
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
            int result = (int)this.Retrieve(valuePtr);
            return result;
        }

        private IntPtr
        Store(int value)
        {
            IntPtr ptr = this.allocator.Alloc(Marshal.SizeOf(typeof(PyObject)));
            CPyMarshal.WriteIntField(ptr, typeof(PyObject), "ob_refcnt", 1);
            CPyMarshal.WritePtrField(ptr, typeof(PyObject), "ob_type", this.PyInt_Type);
            this.map.Associate(ptr, value);
            return ptr;
        }


        public override IntPtr
        PyLong_FromLongLong(long value)
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

        private IntPtr
        Store(double value)
        {
            IntPtr ptr = this.allocator.Alloc(Marshal.SizeOf(typeof(PyObject)));
            CPyMarshal.WriteIntField(ptr, typeof(PyObject), "ob_refcnt", 1);
            CPyMarshal.WritePtrField(ptr, typeof(PyObject), "ob_type", this.PyFloat_Type);
            this.map.Associate(ptr, value);
            return ptr;
        }
        
    }

}
