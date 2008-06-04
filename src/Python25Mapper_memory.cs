
using System;

namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        public override IntPtr
        PyMem_Malloc(int size)
        {
            if (size == 0)
            {
                size = 1;
            }
            try
            {
                return this.allocator.Alloc(size);
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
        
        
    }
}