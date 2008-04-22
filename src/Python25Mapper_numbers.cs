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

        public IntPtr
        Store(int value)
        {
            IntPtr ptr = this.allocator.Alloc(Marshal.SizeOf(typeof(PyObject)));
            CPyMarshal.WriteIntField(ptr, typeof(PyObject), "ob_refcnt", 1);
            CPyMarshal.WritePtrField(ptr, typeof(PyObject), "ob_type", this.PyInt_Type);
            this.StoreUnmanagedData(ptr, value);
            return ptr;
        }


        public override IntPtr
        PyLong_FromLongLong(long value)
        {
            IntPtr result = this.Store((BigInteger)value);
            return result;
        }

        public IntPtr
        Store(BigInteger value)
        {
            // note try/catch
            // proof I don't know C# very well at all
            // pointing and laughing are both fine
            // patching is better
            IntPtr ptr = this.allocator.Alloc(Marshal.SizeOf(typeof(PyObject)));
            CPyMarshal.WriteIntField(ptr, typeof(PyObject), "ob_refcnt", 1);
            CPyMarshal.WritePtrField(ptr, typeof(PyObject), "ob_type", this.PyLong_Type);
            try
            {
                this.StoreUnmanagedData(ptr, value);
                return ptr;
            }
            catch (ArgumentNullException)
            {
                // I think this means that value was null
                // 'if (value == null)'  didn't seem to help
                IntPtr nonePtr = this.objmap[UnmanagedDataMarker.None];
                this.IncRef(nonePtr);
                return nonePtr;
            }
        }
        
        public override IntPtr
        PyFloat_FromDouble(double value)
        {
            return this.Store(value);
        }

        public IntPtr
        Store(double value)
        {
            IntPtr ptr = this.allocator.Alloc(Marshal.SizeOf(typeof(PyObject)));
            CPyMarshal.WriteIntField(ptr, typeof(PyObject), "ob_refcnt", 1);
            CPyMarshal.WritePtrField(ptr, typeof(PyObject), "ob_type", this.PyFloat_Type);
            this.StoreUnmanagedData(ptr, value);
            return ptr;
        }
        
    }

}
