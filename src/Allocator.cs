using System;
using System.Runtime.InteropServices;

namespace Ironclad
{
    public interface IAllocator
    {
        IntPtr Alloc(nint bytes);
        IntPtr Realloc(IntPtr old, nint bytes);
        bool Contains(IntPtr ptr);
        void Free(IntPtr address);
        void FreeAll();
    }

    internal static class IAllocatorExtensions
    {
        public static IntPtr Alloc(this IAllocator allocator, nuint bytes)
            => allocator.Alloc(checked((nint)bytes));

        public static IntPtr Realloc(this IAllocator allocator, IntPtr old, nuint bytes)
            => allocator.Realloc(old, checked((nint)bytes));
    }

    public class HGlobalAllocator : IAllocator
    {
        private StupidSet allocated = new StupidSet();
        
        public virtual IntPtr 
        Alloc(nint bytes)
        {
            IntPtr ptr = Marshal.AllocHGlobal(bytes);
            this.allocated.Add(ptr);
            return ptr;
        }
        
        public virtual IntPtr
        Realloc(IntPtr oldptr, nint bytes)
        {
            IntPtr newptr = Marshal.ReAllocHGlobal(oldptr, bytes);
            this.allocated.SetRemove(oldptr);        
            this.allocated.Add(newptr);
            return newptr;
        }
        
        public virtual bool
        Contains(IntPtr ptr)
        {
            return this.allocated.Contains(ptr);
        }
        
        public virtual void 
        Free(IntPtr ptr)
        {
            this.allocated.SetRemove(ptr);
            Marshal.FreeHGlobal(ptr);
        }
        
        public virtual void 
        FreeAll()
        {
            object[] elements = this.allocated.ElementsArray;
            foreach (object ptr in elements)
            {
                this.Free((IntPtr)ptr);
            }
        }
    }
}
