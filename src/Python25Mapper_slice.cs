using System;
using System.Runtime.InteropServices;

using IronPython.Runtime;

using Ironclad.Structs;

namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        private IntPtr
        Store(Slice slice)
        {
            IntPtr ptr = this.allocator.Alloc(Marshal.SizeOf(typeof(PyObject)));
            CPyMarshal.WriteIntField(ptr, typeof(PyIntObject), "ob_refcnt", 1);
            CPyMarshal.WritePtrField(ptr, typeof(PyIntObject), "ob_type", this.PySlice_Type);
            this.map.Associate(ptr, slice);
            return ptr;
        }
        
    }
}