using System;
using System.Collections.Generic;
using System.Threading;

using IronPython.Runtime;

using Ironclad.Structs;

namespace Ironclad
{
    
    public delegate void PtrFunc(IntPtr ptr);
    
    public class InterestingPtrMap
    {
        private Dictionary<object, IntPtr> id2ptr = new Dictionary<object, IntPtr>();
        private Dictionary<IntPtr, object> ptr2id = new Dictionary<IntPtr, object>();
        private Dictionary<object, object> id2obj = new Dictionary<object, object>();
        
        private Dictionary<WeakReference, IntPtr> ref2ptr = new Dictionary<WeakReference, IntPtr>();
        private Dictionary<IntPtr, WeakReference> ptr2ref = new Dictionary<IntPtr, WeakReference>();
        private StupidSet strongrefs = new StupidSet();
    
        public void Associate(IntPtr ptr, object obj)
        {
            object id = Builtin.id(obj);
            this.ptr2id[ptr] = id;
            this.id2ptr[id] = ptr;
            this.id2obj[id] = obj;
        }
        
        public void BridgeAssociate(IntPtr ptr, object obj)
        {
            WeakReference wref = new WeakReference(obj, true);
            this.ptr2ref[ptr] = wref;
            this.ref2ptr[wref] = ptr;
            this.strongrefs.Add(obj);
        }
        
        private void UpdateStrength(IntPtr ptr, object obj)
        {
            int refcnt = CPyMarshal.ReadIntField(ptr, typeof(PyObject), "ob_refcnt");
            if (refcnt > 1)
            {
                this.Strengthen(obj);
            }
            else
            {
                this.Weaken(obj);
            }
        }
        
        public void UpdateStrength(IntPtr ptr)
        {
            if (this.ptr2id.ContainsKey(ptr))
            {
                // items in this mapping are always strongly referenced
                return;
            }
            this.UpdateStrength(ptr, this.GetObj(ptr));
        }
        
        public void CheckBridgePtrs()
        {
            foreach (KeyValuePair<WeakReference, IntPtr> pair in this.ref2ptr)
            {
                this.UpdateStrength(pair.Value, pair.Key.Target);
            }
        }
        
        public void MapOverBridgePtrs(PtrFunc f)
        {
            Dictionary<IntPtr, WeakReference>.KeyCollection keys = this.ptr2ref.Keys;
            IntPtr[] keysCopy = new IntPtr[keys.Count];
            keys.CopyTo(keysCopy, 0);
            foreach (IntPtr ptr in keysCopy)
            {
                f(ptr);
            }
        }
        
        public void Strengthen(object obj)
        {
            this.strongrefs.Add(obj);
        }
        
        public void Weaken(object obj)
        {
            this.strongrefs.RemoveIfPresent(obj);
        }
        
        public void Release(IntPtr ptr)
        {
            if (this.ptr2id.ContainsKey(ptr))
            {
                object id = this.ptr2id[ptr];
                object obj = this.id2obj[id];
                this.ptr2id.Remove(ptr);
                this.id2obj.Remove(id);
                this.id2ptr.Remove(id);
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
        
        public bool HasObj(object obj)
        {
            if (this.id2ptr.ContainsKey(Builtin.id(obj)))
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
            object id = Builtin.id(obj);
            if (this.id2ptr.ContainsKey(id))
            {
                return this.id2ptr[id];
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
            if (this.ptr2id.ContainsKey(ptr))
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
            if (this.ptr2id.ContainsKey(ptr))
            {
                return this.id2obj[this.ptr2id[ptr]];
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
    
    }
    

}

