
using System;

namespace Ironclad
{
    public partial class PythonMapper : PythonApi
    {
        public override IntPtr
        PyMem_Malloc(nuint size)
        {
            size = size == 0 ? 1 : size;
            try
            {
                return this.allocator.Alloc(size);
            }
            catch (OutOfMemoryException)
            {
                return IntPtr.Zero;
            }
        }

        public override IntPtr
        PyMem_Realloc(IntPtr oldPtr, nuint size)
        {
            size = size == 0 ? 1 : size;
            try
            {
                if (oldPtr == IntPtr.Zero)
                {
                    return this.allocator.Alloc(size);
                }
                return this.allocator.Realloc(oldPtr, size);
            }
            catch (OutOfMemoryException)
            {
                return IntPtr.Zero;
            }
        }
        
        public override void
        PyMem_Free(IntPtr ptr)
        {
            if (ptr != IntPtr.Zero)
            {
                this.allocator.Free(ptr);
            }
        }

        public override IntPtr
        PyObject_Malloc(nuint size)
        {
            return this.PyMem_Malloc(size);
        }

        public override IntPtr
        PyObject_Realloc(IntPtr oldPtr, nuint size)
        {
            return this.PyMem_Realloc(oldPtr, size);
        }
    }
}
