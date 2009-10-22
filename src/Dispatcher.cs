using System;
using System.Runtime.InteropServices;

using IronPython.Modules;
using IronPython.Runtime;
using IronPython.Runtime.Exceptions;

namespace Ironclad
{
    public partial class Dispatcher
    {
        // just pretend this is written in Python
        public PythonMapper mapper;
        public PythonDictionary table;
        private IntPtr modulePtr;
        
        public Dispatcher(PythonMapper inMapper, PythonDictionary inTable) :
            this(inMapper, inTable, IntPtr.Zero)
        {
        }
        
        public Dispatcher(PythonMapper inMapper, PythonDictionary inTable, IntPtr module)
        {
            this.mapper = inMapper;
            this.table = inTable;
            this.modulePtr = module;
        }
        
        public object get_object_field(object instance, int offset)
        {
            this.mapper.EnsureGIL();
            try
            {
                IntPtr instancePtr = this.mapper.Store(instance);
                IntPtr address = CPyMarshal.Offset(instancePtr, offset);
                IntPtr retptr = CPyMarshal.ReadPtr(address);
                object ret = null;
                if (retptr != IntPtr.Zero)
                {
                    ret = this.mapper.Retrieve(retptr);
                }
                this.mapper.DecRef(instancePtr);
                return ret;
            }
            finally
            {
                this.mapper.ReleaseGIL();
            }
        }
        
        public object get_string_field(object instance, int offset)
        {
            this.mapper.EnsureGIL();
            try
            {
                IntPtr instancePtr = this.mapper.Store(instance);
                IntPtr address = CPyMarshal.Offset(instancePtr, offset);
                IntPtr value = CPyMarshal.ReadPtr(address);
                object ret = null;
                if (value != IntPtr.Zero)
                {
                    ret = Marshal.PtrToStringAnsi(value);
                }
                this.mapper.DecRef(instancePtr);
                return ret;
            }
            finally
            {
                this.mapper.ReleaseGIL();
            }
        }
        
        public void set_object_field(object instance, int offset, object value)
        {
            this.mapper.EnsureGIL();
            try
            {
                IntPtr instancePtr = this.mapper.Store(instance);
                IntPtr valuePtr = this.mapper.Store(value);
                IntPtr address = CPyMarshal.Offset(instancePtr, offset);
                IntPtr oldValuePtr = CPyMarshal.ReadPtr(address);
                CPyMarshal.WritePtr(address, valuePtr);
                if (oldValuePtr != IntPtr.Zero)
                {
                    this.mapper.DecRef(oldValuePtr);
                }
                this.mapper.DecRef(instancePtr);
            }
            finally
            {
                this.mapper.ReleaseGIL();
            }
        }

        public void ic_destroy(object arg0)
        {
            if (!this.mapper.Alive)
            {
                return;
            }
            
            this.mapper.EnsureGIL();
            try
            {
                IntPtr ptr0 = this.mapper.Store(arg0);
                int refcnt = this.mapper.RefCount(ptr0);
                if (refcnt != 2)
                {
                    Console.WriteLine("unexpected refcount {0} when deleting object id {1} at {2}", refcnt, Builtin.id(arg0), ptr0.ToString("x"));
                }
                this.mapper.DecRef(ptr0);
                this.mapper.DecRef(ptr0);
                this.mapper.Unmap(ptr0);
                PythonExceptions.BaseException error = (PythonExceptions.BaseException)this.mapper.LastException;
                if (error != null)
                {
                    this.mapper.LastException = null;
                    throw error.clsException;
                }
            }
            catch (Exception e)
            {
                Console.WriteLine("Error on dispose: {0}", e);
            }
            finally
            {
                this.mapper.ReleaseGIL();
            }
        }
    }
}
