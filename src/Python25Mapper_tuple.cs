using System;
using System.Runtime.InteropServices;

using IronPython.Runtime;

using Ironclad.Structs;

namespace Ironclad
{
    public partial class Python25Mapper : PythonMapper
    {
        
        public override IntPtr
        PyTuple_New(int size)
        {
            PyTupleObject tuple = new PyTupleObject();
            tuple.ob_refcnt = 1;
            tuple.ob_type = this.PyTuple_Type;
            tuple.ob_size = (uint)size;
            
            int baseSize = Marshal.SizeOf(typeof(PyTupleObject));
            int extraSize = CPyMarshal.PtrSize * (size - 1);
            IntPtr ptr = this.allocator.Alloc(baseSize + extraSize);
            Marshal.StructureToPtr(tuple, ptr, false);
            this.StoreUnmanagedData(ptr, UnmanagedDataMarker.PyTupleObject);
            return ptr;
        }
    }
}