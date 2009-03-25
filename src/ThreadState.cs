using System;
using System.Runtime.InteropServices;
using System.Threading;

using IronPython.Runtime;
using IronPython.Runtime.Operations;

using Ironclad.Structs;

namespace Ironclad
{
    internal class ThreadState
    {
        private Python25Mapper mapper;
        private IntPtr ptr;
        
        public ThreadState(Python25Mapper mapper)
        {
            this.mapper = mapper;
            uint size = (uint)Marshal.SizeOf(typeof(PyThreadState));
            this.ptr = this.mapper.PyMem_Malloc(size); // leaka leaka leaka
            CPyMarshal.Zero(this.ptr, size);
        }
        
        public IntPtr
        Ptr
        {
            get { return this.ptr; }
        }
        
        public object LastException
        {
            get
            {
                IntPtr typePtr = CPyMarshal.ReadPtrField(this.ptr, typeof(PyThreadState), "curexc_type");
                if (typePtr != IntPtr.Zero)
                {
                    object[] args = new object[0];
                    IntPtr valuePtr = CPyMarshal.ReadPtrField(this.ptr, typeof(PyThreadState), "curexc_value");
                    if (valuePtr != IntPtr.Zero)
                    {
                        args = new object[] { this.mapper.Retrieve(valuePtr) };
                    }
                    return PythonCalls.Call(this.mapper.Retrieve(typePtr), args);
                }
                else
                {
                    return null;
                }
            }
            set
            {
                if ((value as Exception) != null)
                {
                    value = InappropriateReflection.GetPythonException((Exception)value);
                }
                
                
                IntPtr typePtr = CPyMarshal.ReadPtrField(this.ptr, typeof(PyThreadState), "curexc_type");
                if (typePtr != IntPtr.Zero)
                {
                    this.mapper.DecRef(typePtr);
                }
                IntPtr valuePtr = CPyMarshal.ReadPtrField(this.ptr, typeof(PyThreadState), "curexc_value");
                if (valuePtr != IntPtr.Zero)
                {
                    this.mapper.DecRef(valuePtr);
                }
                IntPtr tracebackPtr = CPyMarshal.ReadPtrField(this.ptr, typeof(PyThreadState), "curexc_traceback");
                if (tracebackPtr != IntPtr.Zero)
                {
                    this.mapper.DecRef(tracebackPtr);
                }
                
                // traceback almost completely ignored in ironclad
                CPyMarshal.WritePtrField(this.ptr, typeof(PyThreadState), "curexc_traceback", IntPtr.Zero);
                if (value == null)
                {
                    CPyMarshal.WritePtrField(this.ptr, typeof(PyThreadState), "curexc_type", IntPtr.Zero);
                    CPyMarshal.WritePtrField(this.ptr, typeof(PyThreadState), "curexc_value", IntPtr.Zero);
                }
                else
                {
                    object excType = PythonCalls.Call(Builtin.type, new object[] { value });
                    CPyMarshal.WritePtrField(this.ptr, typeof(PyThreadState), "curexc_type", this.mapper.Store(excType));
                    CPyMarshal.WritePtrField(this.ptr, typeof(PyThreadState), "curexc_value", this.mapper.Store(value.ToString()));
                }
            }
        }


    }
}
