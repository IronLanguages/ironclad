using System;
using System.Collections.Generic;

namespace Ironclad
{
    
    public class InterestingPtrMap
    {
        private Dictionary<object, IntPtr> obj2ptr = new Dictionary<object, IntPtr>();
        private Dictionary<IntPtr, object> ptr2obj = new Dictionary<IntPtr, object>();
        
        private Dictionary<WeakReference, IntPtr> ref2ptr = new Dictionary<WeakReference, IntPtr>();
        private Dictionary<IntPtr, WeakReference> ptr2ref = new Dictionary<IntPtr, WeakReference>();
        private StupidSet strongrefs = new StupidSet();
    
        public void Associate(IntPtr ptr, object obj)
        {
            this.ptr2obj[ptr] = obj;
            this.obj2ptr[obj] = ptr;
        }
        
        public void Associate(IntPtr ptr, UnmanagedDataMarker udm)
        {
            this.ptr2obj[ptr] = udm;
        }
        
        public void WeakAssociate(IntPtr ptr, object obj)
        {
            WeakReference wref = new WeakReference(obj, true);
            this.ptr2ref[ptr] = wref;
            this.ref2ptr[wref] = ptr;
        }
        
        public void Strengthen(object obj)
        {
            this.strongrefs.Add(obj);
        }
        
        public void Weaken(object obj)
        {
            this.strongrefs.RemoveIfPresent(obj);
        }
        
        public object[] GetStrongRefs()
        {
            return this.strongrefs.ElementsArray;
        }
        
        public bool HasObj(object obj)
        {
            if (this.obj2ptr.ContainsKey(obj))
            {
                return true;
            }
            foreach (WeakReference wref in this.ref2ptr.Keys)
            {
                if (Object.ReferenceEquals(obj, wref.Target))
                {
                    return true;
                }
            }
            return false;
        }
        
        public IntPtr GetPtr(object obj)
        {
            if (this.obj2ptr.ContainsKey(obj))
            {
                return this.obj2ptr[obj];
            }
            foreach (WeakReference wref in this.ref2ptr.Keys)
            {
                if (Object.ReferenceEquals(obj, wref.Target))
                {
                    return this.ref2ptr[wref];
                }
            }
            throw new KeyNotFoundException(String.Format("No obj-to-ptr mapping for {0}", obj));
        }
        
        public bool HasPtr(IntPtr ptr)
        {
            if (this.ptr2obj.ContainsKey(ptr))
            {
                return true;
            }
            if (this.ptr2ref.ContainsKey(ptr))
            {
                return true;
            }
            return false;
        }
        
        public object GetObj(IntPtr ptr)
        {
            if (this.ptr2obj.ContainsKey(ptr))
            {
                return this.ptr2obj[ptr];
            }
            if (this.ptr2ref.ContainsKey(ptr))
            {
                WeakReference wref = this.ptr2ref[ptr];
                if (wref.IsAlive)
                {
                    return wref.Target;
                }
                throw new NullReferenceException(String.Format("Weakly mapped object for ptr {0} was apparently GCed too soon", ptr));
            }
            throw new KeyNotFoundException(String.Format("No ptr-to-obj mapping for {0}", ptr));
        }
        
        public void Release(IntPtr ptr)
        {
            if (this.ptr2obj.ContainsKey(ptr))
            {
                object obj = this.ptr2obj[ptr];
                this.ptr2obj.Remove(ptr);
                if (this.obj2ptr.ContainsKey(obj))
                {
                    this.obj2ptr.Remove(obj);
                }
            }
            else if (this.ptr2ref.ContainsKey(ptr))
            {
                WeakReference wref = this.ptr2ref[ptr];
                this.ptr2ref.Remove(ptr);
                this.ref2ptr.Remove(wref);
                if (wref.IsAlive)
                {
                    this.strongrefs.RemoveIfPresent(wref.Target);
                }
            }
            else
            {
                throw new KeyNotFoundException(String.Format("tried to release unmapped ptr {0}", ptr));
            }
        }
    
    }
    

}

