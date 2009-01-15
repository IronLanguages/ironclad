using System;
using System.Collections.Generic;
using System.Diagnostics;
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
        private Dictionary<object, bool> id2reffed = new Dictionary<object, bool>();
        private StupidSet strongrefs = new StupidSet();
        
        private int cbpCount = 0;
        private int cbpRegulator = 500;
    
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
            
            WeakReference wref = new WeakReference(obj);
            this.id2ref[id] = wref;
            this.id2reffed[id] = true;
            this.strongrefs.Add(obj);
        }
        
        public void UpdateStrength(IntPtr ptr)
        {
            object id = this.ptr2id[ptr];
            if (!this.id2ref.ContainsKey(id))
            {
                return;
            }
            
            object obj = this.id2ref[id].Target;
            int refcnt = CPyMarshal.ReadInt(ptr);
            if (refcnt > 1)
            {
                this.Strengthen(obj);
            }
            else
            {
                this.Weaken(obj);
            }
        }
        
        public int GCThreshold
        {
            get {
                return this.cbpRegulator;
            }
            set {
                this.cbpRegulator = value;
            }
        }
        
        
        public void CheckBridgePtrs(bool force)
        {
            if (!force)
            {
                // throttling and forced GC not tested; couldn't work out how
                this.cbpCount += 1;
                if (this.cbpCount < this.cbpRegulator)
                {
                    return;
                }
                this.cbpCount = 0;
            }
            this.MapOverBridgePtrs(new PtrFunc(this.UpdateStrength));
            GC.Collect();
        }
        
        public void MapOverBridgePtrs(PtrFunc f)
        {
            object[] keys = new object[this.id2ref.Count];
            this.id2ref.Keys.CopyTo(keys, 0);
            foreach (object id in keys)
            {
                f(this.id2ptr[id]);
            }
            return;
        }
        
        public void Strengthen(object obj)
        {
            object id = Builtin.id(obj);
            if (this.id2ref.ContainsKey(id))
            {
                if (this.id2reffed.ContainsKey(id))
                {
                    if (this.id2reffed[id] == true)
                    {
                        // already strongly reffed
                        return; 
                    }
                }
                this.strongrefs.Add(obj);
                this.id2reffed[id] = true;
            }
        }
        
        public void Weaken(object obj)
        {
            object id = Builtin.id(obj);
            if (this.id2ref.ContainsKey(id))
            {
                if (this.id2reffed.ContainsKey(id))
                {
                    if (this.id2reffed[id] == false)
                    {
                        // already weakly reffed
                        return; 
                    }
                }
                this.strongrefs.RemoveIfPresent(obj);
                this.id2reffed[id] = false;
            }
        }
        
        public void Release(IntPtr ptr)
        {
            if (!this.ptr2id.ContainsKey(ptr))
            {
                throw new BadMappingException(String.Format("Release: tried to release unmapped ptr {0}", ptr.ToString("x")));
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
                
                bool needsRemove = this.id2reffed[id];
                this.id2reffed.Remove(id);
                if (needsRemove)
                {
                    object obj = wref.Target;
                    if (obj == null)
                    {
                        throw new NullReferenceException(String.Format(
                            "Release: object for ptr {0} was GCed early (in an 'impossible' way)", ptr.ToString("x")));
                    }
                    else
                    {
                        this.strongrefs.SetRemove(obj);
                    }
                }
            }
            else
            {
                throw new BadMappingException(String.Format("Release: mapping corrupt (ptr {0})", ptr.ToString("x")));
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
                throw new BadMappingException(String.Format("GetPtr: No obj-to-ptr mapping for {0}", obj));
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
                throw new BadMappingException(String.Format("GetObj: No ptr-to-obj mapping for {0}", ptr.ToString("x")));
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
                throw new NullReferenceException(
                    String.Format("GetObj: Weakly mapped object for ptr {0} was GCed too soon", ptr.ToString("x")));
            }
            else
            {
                throw new BadMappingException(String.Format("GetObj: mapping corrupt (ptr {0})", ptr.ToString("x")));
            }
        }
    }
}

