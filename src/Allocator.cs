using System;
using System.Collections.Generic;
using System.Linq;
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
        private readonly HashSet<IntPtr> allocated = new HashSet<IntPtr>();
        
        private void RemoveAllocated(IntPtr ptr)
        {
            if (!this.allocated.Remove(ptr))
            {
                throw new KeyNotFoundException(String.Format("{0} was not present in set, and hence could not be removed.", ptr));
            }
        }

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
            RemoveAllocated(oldptr);
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
            RemoveAllocated(ptr);
            Marshal.FreeHGlobal(ptr);
        }
        
        public virtual void 
        FreeAll()
        {
            foreach (var ptr in this.allocated.ToArray())
            {
                Free(ptr);
            }
        }
    }
}
