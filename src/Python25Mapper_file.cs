using System;
using System.IO;
using System.Runtime.InteropServices;

using IronPython.Runtime;

using Ironclad.Structs;

namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        public override IntPtr PyFile_AsFile(IntPtr pyFilePtr)
        {
            if (this.FILEs.ContainsKey(pyFilePtr))
            {
                return this.FILEs[pyFilePtr];
            }
            
            PythonFile pyFile = (PythonFile)this.Retrieve(pyFilePtr);
            FileStream stream = InappropriateReflection.StreamFromPythonFile(pyFile);
            SafeHandle safeHandle = stream.SafeFileHandle;
            IntPtr handle = safeHandle.DangerousGetHandle();
            
            int fd = Unmanaged._open_osfhandle(handle, 0);
            IntPtr FILE = IntPtr.Zero;
            if (stream.CanWrite)
            {
                FILE = Unmanaged._fdopen(fd, "w");
            }
            else
            {
                FILE = Unmanaged._fdopen(fd, "r");
            }
            this.FILEs[pyFilePtr] = FILE;
            return FILE;
        }    
        
        
        private IntPtr
        Store(PythonFile obj)
        {
            IntPtr ptr = this.allocator.Alloc(Marshal.SizeOf(typeof(PyObject)));
            CPyMarshal.WriteIntField(ptr, typeof(PyObject), "ob_refcnt", 1);
            CPyMarshal.WritePtrField(ptr, typeof(PyObject), "ob_type", this.PyFile_Type);
            this.map.Associate(ptr, obj);
            return ptr;
        }  

        
        public virtual void 
        PyFile_Dealloc(IntPtr ptr)
        {
            if (this.FILEs.ContainsKey(ptr))
            {
                Unmanaged.fclose(this.FILEs[ptr]);
                this.FILEs.Remove(ptr);
            }
            IntPtr _type = CPyMarshal.ReadPtrField(ptr, typeof(PyObject), "ob_type");
            PyObject_Free_Delegate freeDgt = (PyObject_Free_Delegate)
                CPyMarshal.ReadFunctionPtrField(
                    _type, typeof(PyTypeObject), "tp_free", typeof(PyObject_Free_Delegate));
            freeDgt(ptr);
        }
        
    }
}
