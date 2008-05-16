using System;
using System.Runtime.InteropServices;

namespace Ironclad
{
    public interface IAllocator
    {
        IntPtr Alloc(int bytes);
        IntPtr Realloc(IntPtr old, int bytes);
        void Free(IntPtr address);
        void FreeAll();
    }
    
    public class HGlobalAllocator : IAllocator
    {
        private StupidSet allocated = new StupidSet();
        
        public virtual IntPtr 
        Alloc(int bytes)
        {
            IntPtr ptr = Marshal.AllocHGlobal(bytes);
            this.allocated.Add(ptr);
            return ptr;
        }
        
        public virtual IntPtr
        Realloc(IntPtr oldptr, int bytes)
        {
            IntPtr newptr = Marshal.ReAllocHGlobal(oldptr, (IntPtr)bytes);    
            this.allocated.SetRemove(oldptr);        
            this.allocated.Add(newptr);
            return newptr;
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