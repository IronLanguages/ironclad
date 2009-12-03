using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Threading;

using IronPython.Modules;
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
        private Dictionary<IntPtr, long> ptr2id = new Dictionary<IntPtr, long>();
        private Dictionary<long, IntPtr> id2ptr = new Dictionary<long, IntPtr>();
        private Dictionary<long, object> id2obj = new Dictionary<long, object>();

        private Dictionary<long, WeakReference> id2wref = new Dictionary<long, WeakReference>();
        private Dictionary<long, object> id2sref = new Dictionary<long, object>();
        
        private int cbpCount = 0;
        private int cbpRegulator = 50000;
    
        public void
        Associate(IntPtr ptr, object obj)
        {
            long id = PythonOps.Id(obj);
            this.ptr2id[ptr] = id;
            this.id2ptr[id] = ptr;
            this.id2obj[id] = obj;
        }
        
        public void
        BridgeAssociate(IntPtr ptr, object obj)
        {
            long id = PythonOps.Id(obj);
            this.ptr2id[ptr] = id;
            this.id2ptr[id] = ptr;
            
            WeakReference wref = new WeakReference(obj);
            this.id2wref[id] = wref;
            this.id2sref[id] = obj;
        }
        
        public void
        UpdateStrength(IntPtr ptr)
        {
            long id = this.ptr2id[ptr];
            if (!this.id2wref.ContainsKey(id))
            {
                return;
            }
            
            object obj = this.id2wref[id].Target;
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
        
        
        public void
        LogMappingInfo(object id_)
        {
            long id = (long)id_;
            if (this.id2ptr.ContainsKey(id))
            {
                IntPtr ptr = this.id2ptr[id];
                Console.WriteLine("object for id {0} is stored at {1}; refcount is {2}", 
                    id, ptr.ToString("x"), CPyMarshal.ReadInt(ptr));
                if (this.id2obj.ContainsKey(id))
                {
                    Console.WriteLine("object is simply mapped");
                    Console.WriteLine(PythonCalls.Call(Builtin.str, new object[] { this.id2obj[id] }));
                }
                else if (this.id2wref.ContainsKey(id))
                {
                    this.UpdateStrength(ptr);
                    Console.WriteLine("object is cleverly mapped");
                    if (this.id2sref.ContainsKey(id))
                    {
                        Console.WriteLine("object is being kept alive");
                    }
                    else
                    {   
                        Console.WriteLine("object is at GC's mercy");
                    }
                }
                else
                {
                    Console.WriteLine("hm, object has been lost somewhere");
                }
            }
            else
            {
                Console.WriteLine("{0} is not mapped", id);
            }
        }
        
        public void
        LogRefs()
        {
            int wtotal = 0;
            int stotal = 0;
            Dictionary<object, int> scounts = new Dictionary<object, int>();
            Dictionary<object, int> wcounts = new Dictionary<object, int>();
            wcounts["ZOMBIE"] = 0;
            foreach (long id in this.id2wref.Keys)
            {
                if (!this.id2sref.ContainsKey(id))
                {
                    wtotal += 1;
                    WeakReference wref = this.id2wref[id];
                    if (wref.IsAlive)
                    {
                        object type_ = PythonCalls.Call(Builtin.type, new object[] { wref.Target });
                        if (!wcounts.ContainsKey(type_))
                        {
                            wcounts[type_] = 0;
                        }
                        wcounts[type_] += 1;
                    }
                    else
                    {
                        wcounts["ZOMBIE"] += 1;
                    }
                }
                else
                {
                    stotal += 1;
                    object type_ = PythonCalls.Call(Builtin.type, new object[] { this.id2sref[id] });
                    if (!scounts.ContainsKey(type_))
                    {
                        scounts[type_] = 0;
                    }
                    scounts[type_] += 1;
                }
            }
            Console.WriteLine("weak refs: {0}", wtotal);
            foreach (object type_ in wcounts.Keys)
            {
                Console.WriteLine("{0}: {1}", PythonCalls.Call(Builtin.str, new object[] { type_ }), wcounts[type_]);
            }
            
            Console.WriteLine("strong refs: {0}", stotal);
            foreach (object type_ in scounts.Keys)
            {
                Console.WriteLine("{0}: {1}", PythonCalls.Call(Builtin.str, new object[] { type_ }), scounts[type_]);
            }
        }
        
        
        public int
        GCThreshold
        {
            get { return this.cbpRegulator; }
            set { this.cbpRegulator = value; }
        }
        
        
        public void
        CheckBridgePtrs(bool force)
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
        }
        
        public void
        MapOverBridgePtrs(PtrFunc f)
        {
            long[] keys = new long[this.id2wref.Count];
            this.id2wref.Keys.CopyTo(keys, 0);
            foreach (long id in keys)
            {
                f(this.id2ptr[id]);
            }
            return;
        }
        
        public void
        Strengthen(object obj)
        {
            long id = PythonOps.Id(obj);
            if (this.id2wref.ContainsKey(id))
            {
                if (this.id2sref.ContainsKey(id))
                {
                    // already strongly reffed
                    return; 
                }
                this.id2sref[id] = obj;
            }
        }
        
        public void
        Weaken(object obj)
        {
            long id = PythonOps.Id(obj);
            if (this.id2wref.ContainsKey(id))
            {
                if (!this.id2sref.ContainsKey(id))
                {
                    // already weakly reffed
                    return; 
                }
                this.id2sref.Remove(id);
            }
        }
        
        public void
        Release(IntPtr ptr)
        {
            if (!this.ptr2id.ContainsKey(ptr))
            {
                throw new BadMappingException(String.Format("Release: tried to release unmapped ptr {0}", ptr.ToString("x")));
            }

            long id = this.ptr2id[ptr];
            this.ptr2id.Remove(ptr);
            this.id2ptr.Remove(id);

            if (this.id2obj.ContainsKey(id))
            {
                this.id2obj.Remove(id);
            }
            else if (this.id2wref.ContainsKey(id))
            {
                this.id2wref.Remove(id);
                if (this.id2sref.ContainsKey(id))
                {
                    this.id2sref.Remove(id);
                }
            }
            else
            {
                throw new BadMappingException(String.Format("Release: mapping corrupt (ptr {0})", ptr.ToString("x")));
            }
        }
        
        public bool
        HasObj(object obj)
        {
            if (this.id2ptr.ContainsKey(PythonOps.Id(obj)))
            {
                return true;
            }
            return false;
        }
        
        public IntPtr
        GetPtr(object obj)
        {
            long id = PythonOps.Id(obj);
            if (!this.id2ptr.ContainsKey(id))
            {
                throw new BadMappingException(String.Format("GetPtr: No obj-to-ptr mapping for {0}", obj));
            }
            return this.id2ptr[id];
        }
        
        public bool
        HasPtr(IntPtr ptr)
        {
            if (this.ptr2id.ContainsKey(ptr))
            {
                return true;
            }
            return false;
        }
        
        public object
        GetObj(IntPtr ptr)
        {
            if (!this.ptr2id.ContainsKey(ptr))
            {
                throw new BadMappingException(String.Format("GetObj: No ptr-to-obj mapping for {0}", ptr.ToString("x")));
            }

            long id = this.ptr2id[ptr];
            if (this.id2obj.ContainsKey(id))
            {
                return this.id2obj[id];
            }
            else if (this.id2sref.ContainsKey(id))
            {
                return this.id2sref[id];
            }
            else if (this.id2wref.ContainsKey(id))
            {
                WeakReference wref = this.id2wref[id];
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


