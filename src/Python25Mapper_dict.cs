using System;
using System.Collections;
using System.Runtime.InteropServices;

using IronPython.Runtime;
using IronPython.Runtime.Calls;
using IronPython.Runtime.Types;

using Ironclad.Structs;

namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        
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
                return proxy.__len__();
            }
            return dict.Keys.Count;
        }
        
        
        private IntPtr
        PyDict_Get(IntPtr dictPtr, object key)
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
            return PyDict_Get(dictPtr, this.Retrieve(keyPtr));
        }
        
        
        public override IntPtr
        PyDict_GetItemString(IntPtr dictPtr, string key)
        {
            return PyDict_Get(dictPtr, key);
        }


        private int 
        PyDict_Set(IntPtr dictPtr, object key, object item)
        {
            IDictionary dict = (IDictionary)this.Retrieve(dictPtr);
            if (dict is DictProxy)
            {
                PythonType _type = InappropriateReflection.PythonTypeFromDictProxy((DictProxy)dict);
                Builtin.setattr(DefaultContext.Default, _type, (string)key, item);
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
                return this.PyDict_Set(dictPtr, this.Retrieve(keyPtr), this.Retrieve(itemPtr));
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
            return this.PyDict_Set(dictPtr, key, this.Retrieve(itemPtr));
        }
    }
}