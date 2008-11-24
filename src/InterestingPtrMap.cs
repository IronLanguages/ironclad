using System;
using System.Collections.Generic;
using System.Threading;

using IronPython.Runtime;
using IronPython.Runtime.Operations;

using Ironclad.Structs;

namespace Ironclad
{

    public class BadMappingException : Exception
    {
        public BadMappingException(string message): base(message)
        {
        }
    }
    
    public delegate void PtrFunc(IntPtr ptr);
    
    public class InterestingPtrMap
    {
        private Dictionary<IntPtr, object> ptr2id = new Dictionary<IntPtr, object>();
        private Dictionary<object, IntPtr> id2ptr = new Dictionary<object, IntPtr>();
        private Dictionary<object, object> id2obj = new Dictionary<object, object>();
        private Dictionary<object, WeakReference> id2ref = new Dictionary<object, WeakReference>();
        private StupidSet strongrefs = new StupidSet();
        private int cbpThrottle = 0;
    
        public void Associate(IntPtr ptr, object obj)
        {
            object id = Builtin.id(obj);
            this.ptr2id[ptr] = id;
            this.id2ptr[id] = ptr;
            
            this.id2obj[id] = obj;
        }
        
        public void BridgeAssociate(IntPtr ptr, object obj)
        {
            object id = Builtin.id(obj);
            this.ptr2id[ptr] = id;
            this.id2ptr[id] = ptr;
            
            WeakReference wref = new WeakReference(obj, true);
            this.id2ref[id] = wref;
            this.strongrefs.Add(obj);
        }
        
        public void UpdateStrength(IntPtr ptr)
        {
            object obj = this.GetObj(ptr);
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
        
        public void CheckBridgePtrs()
        {
            this.cbpThrottle += 1;
            if (this.cbpThrottle < 50)
            {
                return;
            }
            this.cbpThrottle = 0;
            this.MapOverBridgePtrs(new PtrFunc(this.UpdateStrength));
        }
        
        public void MapOverBridgePtrs(PtrFunc f)
        {
            Dictionary<IntPtr, object>.KeyCollection keys = this.ptr2id.Keys;
            IntPtr[] keysCopy = new IntPtr[keys.Count];
            keys.CopyTo(keysCopy, 0);
            foreach (IntPtr ptr in keysCopy)
            {
                if (this.ptr2id.ContainsKey(ptr))
                {
                    if (this.id2ref.ContainsKey(this.ptr2id[ptr]))
                    {
                        f(ptr);
                    }
                }
            }
        }
        
        public void Strengthen(object obj)
        {
            object id = Builtin.id(obj);
            if (this.id2ref.ContainsKey(id))
            {
                this.strongrefs.Add(obj);
            }
        }
        
        public void Weaken(object obj)
        {
            object id = Builtin.id(obj);
            if (this.id2ref.ContainsKey(id))
            {
                this.strongrefs.RemoveIfPresent(obj);
            }
        }
        
        public void Release(IntPtr ptr)
        {
            if (!this.ptr2id.ContainsKey(ptr))
            {
                throw new BadMappingException(String.Format("tried to release unmapped ptr {0}", ptr.ToString("x")));
            }
            
            object id = this.ptr2id[ptr];
            this.ptr2id.Remove(ptr);
            this.id2ptr.Remove(id);

            if (this.id2obj.ContainsKey(id))
            {
                this.id2obj.Remove(id);
            }
            else if (this.id2ref.ContainsKey(id))
            {
                WeakReference wref = this.id2ref[id];
                this.id2ref.Remove(id);
                if (wref.IsAlive)
                {
                    this.strongrefs.RemoveIfPresent(wref.Target);
                }
            }
            else
            {
                throw new BadMappingException(String.Format("mapping corrupt (ptr {0})", ptr.ToString("x")));
            }
        }
        
        public bool HasObj(object obj)
        {
            if (this.id2ptr.ContainsKey(Builtin.id(obj)))
            {
                return true;
            }
            return false;
        }
        
        public IntPtr GetPtr(object obj)
        {
            object id = Builtin.id(obj);
            if (!this.id2ptr.ContainsKey(id))
            {
                throw new BadMappingException(String.Format("No obj-to-ptr mapping for {0}", obj));
            }
            return this.id2ptr[id];
        }
        
        public bool HasPtr(IntPtr ptr)
        {
            if (this.ptr2id.ContainsKey(ptr))
            {
                return true;
            }
            return false;
        }
        
        public object GetObj(IntPtr ptr)
        {
            if (!this.ptr2id.ContainsKey(ptr))
            {
                throw new BadMappingException(String.Format("No ptr-to-obj mapping for {0}", ptr.ToString("x")));
            }
            
            object id = this.ptr2id[ptr];
            if (this.id2obj.ContainsKey(id))
            {
                return this.id2obj[id];
            }
            else if (this.id2ref.ContainsKey(id))
            {
                WeakReference wref = this.id2ref[id];
                if (wref.IsAlive)
                {
                    return wref.Target;
                }
                throw new NullReferenceException(String.Format("Weakly mapped object for ptr {0} was apparently GCed too soon", ptr.ToString("x")));
            }
            else
            {
                throw new BadMappingException(String.Format("mapping corrupt (ptr {0})", ptr.ToString("x")));
            }
        }
    }
}

