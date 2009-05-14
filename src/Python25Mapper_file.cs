using System;
using System.IO;
using System.Runtime.InteropServices;

using IronPython.Runtime;

using Ironclad.Structs;

namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        public override IntPtr
        IC_PyFile_AsFile(IntPtr pyFilePtr)
        {
            try
            {
                if (this.FILEs.ContainsKey(pyFilePtr))
                {
                    return this.FILEs[pyFilePtr];
                }

                PythonFile pyFile = (PythonFile)this.Retrieve(pyFilePtr);
                int fd = this.ConvertPyFileToDescriptor(pyFile);
                IntPtr FILE = IntPtr.Zero;
                if (InappropriateReflection.StreamFromPythonFile(pyFile).CanWrite)
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
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }

        public int
        ConvertPyFileToDescriptor(PythonFile pyFile)
        {
            FileStream stream = InappropriateReflection.StreamFromPythonFile(pyFile);
            SafeHandle safeHandle = stream.SafeFileHandle;
            IntPtr handle = safeHandle.DangerousGetHandle();
            return Unmanaged._open_osfhandle(handle, 0);
        }

        private IntPtr
        Store(PythonFile obj)
        {
            IntPtr ptr = this.allocator.Alloc((uint)Marshal.SizeOf(typeof(PyFileObject)));
            CPyMarshal.Zero(ptr, Marshal.SizeOf(typeof(PyFileObject)));
            CPyMarshal.WriteIntField(ptr, typeof(PyObject), "ob_refcnt", 1);
            CPyMarshal.WritePtrField(ptr, typeof(PyObject), "ob_type", this.PyFile_Type);
            CPyMarshal.WriteIntField(ptr, typeof(PyFileObject), "f_fp", -2);
            this.map.Associate(ptr, obj);
            return ptr;
        }
        
        public override void 
        IC_file_dealloc(IntPtr ptr)
        {
            if (this.FILEs.ContainsKey(ptr))
            {
                Unmanaged.fclose(this.FILEs[ptr]);
                this.FILEs.Remove(ptr);
            }
            IntPtr _type = CPyMarshal.ReadPtrField(ptr, typeof(PyObject), "ob_type");
            dgt_void_ptr freeDgt = (dgt_void_ptr)
                CPyMarshal.ReadFunctionPtrField(
                    _type, typeof(PyTypeObject), "tp_free", typeof(dgt_void_ptr));
            freeDgt(ptr);
        }
        
    }
}
