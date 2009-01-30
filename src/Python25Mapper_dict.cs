using System;
using System.Collections;
using System.Runtime.InteropServices;

using IronPython.Runtime;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;

using Ironclad.Structs;

namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        
        private void CreateKindaDictProxy()
        {
            // can't contruct types.DictProxy, and ipy DictProxy class wraps a type, not a dict
            this.ExecInModule(CodeSnippets.KINDA_DICT_PROXY_CODE, this.scratchModule);
            this.kindaDictProxyClass = ScopeOps.__getattribute__(this.scratchModule, "KindaDictProxy");
        }
        
        public override IntPtr
        PyDict_New()
        {
            return this.Store(new PythonDictionary());
        }
        
        private IntPtr
        Store(IDictionary dictMgd)
        {
            PyObject dict = new PyObject();
            dict.ob_refcnt = 1;
            dict.ob_type = this.PyDict_Type;
            IntPtr dictPtr = this.allocator.Alloc(Marshal.SizeOf(typeof(PyObject)));
            Marshal.StructureToPtr(dict, dictPtr, false);
            this.map.Associate(dictPtr, dictMgd);
            return dictPtr;
        }
        
        public override int
        PyDict_Size(IntPtr dictPtr)
        {
            IDictionary dict = (IDictionary)this.Retrieve(dictPtr);
            if (dict is DictProxy)
            {
                DictProxy proxy = (DictProxy)dict;
                return proxy.__len__(this.scratchContext);
            }
            return dict.Keys.Count;
        }
        
        
        public override IntPtr
        PyDictProxy_New(IntPtr mappingPtr)
        {
            return this.Store(PythonCalls.Call(this.kindaDictProxyClass, this.Retrieve(mappingPtr)));
        }
        
        
        private IntPtr
        IC_PyDict_Get(IntPtr dictPtr, object key)
        {
            IDictionary dict = (IDictionary)this.Retrieve(dictPtr);
            if (dict.Contains(key))
            {
                IntPtr result = this.Store(dict[key]);
                this.RememberTempObject(result);
                return result;
            }
            return IntPtr.Zero;
        }
        
        
        public override IntPtr
        PyDict_GetItem(IntPtr dictPtr, IntPtr keyPtr)
        {
            return this.IC_PyDict_Get(dictPtr, this.Retrieve(keyPtr));
        }
        
        
        public override IntPtr
        PyDict_GetItemString(IntPtr dictPtr, string key)
        {
            return this.IC_PyDict_Get(dictPtr, key);
        }


        private int 
        IC_PyDict_Set(IntPtr dictPtr, object key, object item)
        {
            IDictionary dict = (IDictionary)this.Retrieve(dictPtr);
            if (dict is DictProxy)
            {
                PythonType _type = InappropriateReflection.PythonTypeFromDictProxy((DictProxy)dict);
                Builtin.setattr(this.scratchContext, _type, (string)key, item);
            }
            else
            {
                dict[key] = item;
            }
            return 0;
        }


        public override int
        PyDict_SetItem(IntPtr dictPtr, IntPtr keyPtr, IntPtr itemPtr)
        {
            try
            {
                return this.IC_PyDict_Set(dictPtr, this.Retrieve(keyPtr), this.Retrieve(itemPtr));
            }
            catch (Exception e)
            {
                this.LastException = e;
                return -1;
            }
        }
        
        public override int
        PyDict_SetItemString(IntPtr dictPtr, string key, IntPtr itemPtr)
        {
            return this.IC_PyDict_Set(dictPtr, key, this.Retrieve(itemPtr));
        }
        
        private int
        IC_PyDict_Del(IntPtr dictPtr, object key)
        {
            IDictionary dict = (IDictionary)this.Retrieve(dictPtr);
            // induce a TypeError, in case key is unhashable
            PythonOps.Hash(this.scratchContext, key);
            if (dict.Contains(key))
            {
                dict.Remove(key);
                return 0;
            }
            return -1;
        }

        public override int
        PyDict_DelItem(IntPtr dictPtr, IntPtr keyPtr)
        {
            try
            {
                object key = this.Retrieve(keyPtr);
                return this.IC_PyDict_Del(dictPtr, key);
            }
            catch (Exception e)
            {
                this.LastException = e;
                return -1;
            }
        }

        public override int
        PyDict_DelItemString(IntPtr dictPtr, string key)
        {
            return this.IC_PyDict_Del(dictPtr, key);
        }

        public override IntPtr
        PyDict_Values(IntPtr dictPtr)
        {
            IDictionary dict = (IDictionary)this.Retrieve(dictPtr);
            List values = new List();
            values.__init__(dict.Values);
            return this.Store(values);
        }
        
        public override int
        PyDict_Next(IntPtr dictPtr, IntPtr posPtr, IntPtr keyPtrPtr, IntPtr valuePtrPtr)
        {
            // note: this is not efficient, and assumes constant ordering of results from 
            // KeyCollection.GetEnumerator. Storing an iterator would probably work,
            // but we can't work out how to not leak it if iteration does not complete.
            try
            {
                IDictionary dict = (IDictionary)this.Retrieve(dictPtr);
                IEnumerator keys = dict.Keys.GetEnumerator();
                int pos = CPyMarshal.ReadInt(posPtr);
                for (int i = 0; i <= pos; i++)
                {
                    if (!keys.MoveNext())
                    {
                        return 0;
                    }
                }

                object key = keys.Current;
                IntPtr keyPtr = this.Store(key);
                this.RememberTempObject(keyPtr);
                CPyMarshal.WritePtr(keyPtrPtr, keyPtr);
                
                IntPtr valuePtr = this.Store(dict[key]);
                this.RememberTempObject(valuePtr);
                CPyMarshal.WritePtr(valuePtrPtr, valuePtr);
                
                CPyMarshal.WriteInt(posPtr, pos + 1);
                return 1;
            }
            catch (Exception e)
            {
                this.LastException = e;
                return 0;
            }
        }
        
    }
}
