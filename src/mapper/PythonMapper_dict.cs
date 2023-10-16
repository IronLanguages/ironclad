using System;
using System.Collections;
using System.Runtime.InteropServices;

using IronPython.Modules;
using IronPython.Runtime;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;

using Ironclad.Structs;

namespace Ironclad
{
    public partial class PythonMapper : PythonApi
    {
        
        public override IntPtr
        PyDict_New()
        {
            return this.Store(new PythonDictionary());
        }
        
        public override int
        IC_PyDict_Init(IntPtr _, IntPtr __, IntPtr ___)
        {
            // _ctypes has some excuse for calling this; we don't normally expect it to be called
            // probably no longer needed
            return 0;
        }
        
        private IntPtr
        StoreTyped(IDictionary dictMgd)
        {
            PyObject dict = new PyObject();
            dict.ob_refcnt = 1;
            dict.ob_type = this.PyDict_Type;
            IntPtr dictPtr = this.allocator.Alloc(Marshal.SizeOf<PyObject>());
            Marshal.StructureToPtr(dict, dictPtr, false);
            this.map.Associate(dictPtr, dictMgd);
            return dictPtr;
        }
        
        public override nint
        PyDict_Size(IntPtr dictPtr)
        {
            IDictionary dict = (IDictionary)this.Retrieve(dictPtr);
            if (dict is MappingProxy proxy)
            {
                return proxy.__len__(this.scratchContext);
            }
            return dict.Keys.Count;
        }
        
        public override int
        PyDict_Update(IntPtr dstPtr, IntPtr srcPtr)
        {
            try
            {
                PythonDictionary dst = (PythonDictionary)this.Retrieve(dstPtr);
                dst.update(this.scratchContext, this.Retrieve(srcPtr));
                return 0;
            }
            catch (Exception e)
            {
                this.LastException = e;
                return -1;
            }
        }

        public override IntPtr
        PyDict_Copy(IntPtr dictPtr)
        {
            try
            {
                PythonDictionary dict = (PythonDictionary)this.Retrieve(dictPtr);
                return this.Store(dict.copy(this.scratchContext));
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }
        
        public override IntPtr
        PyDictProxy_New(IntPtr mappingPtr)
        {
            return this.Store(PythonCalls.Call(this.kindaDictProxy, this.Retrieve(mappingPtr)));
        }
        
        
        private IntPtr
        IC_PyDict_Get(IntPtr dictPtr, object key)
        {
            IDictionary dict = (IDictionary)this.Retrieve(dictPtr);
            if (dict.Contains(key))
            {
                IntPtr result = this.Store(dict[key]);
                this.DecRefLater(result);
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

        public override IntPtr
        PyDict_GetItemWithError(IntPtr dictPtr, IntPtr keyPtr)
        {
            // TODO: WithError...
            return this.IC_PyDict_Get(dictPtr, this.Retrieve(keyPtr));
        }

        private int 
        IC_PyDict_Set(IntPtr dictPtr, object key, object item)
        {
            IDictionary dict = (IDictionary)this.Retrieve(dictPtr);
            if (dict is MappingProxy proxy)
            {
                PythonType _type = InappropriateReflection.PythonTypeFromMappingProxy(proxy);
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
            PythonList values = new PythonList();
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
                this.DecRefLater(keyPtr);
                CPyMarshal.WritePtr(keyPtrPtr, keyPtr);
                
                IntPtr valuePtr = this.Store(dict[key]);
                this.DecRefLater(valuePtr);
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
        
        public override IntPtr _PyDict_GetItemId(IntPtr arg0, IntPtr arg1)
        {
            var id = Marshal.PtrToStructure<_Py_Identifier>(arg1);
            var key = Marshal.PtrToStringAnsi(id.@string);
            return PyDict_GetItemString(arg0, key);
        }
    }
}
