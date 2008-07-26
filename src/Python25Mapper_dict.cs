using System;
using System.Runtime.InteropServices;

using IronPython.Runtime;
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
        Store(PythonDictionary dictMgd)
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
            PythonDictionary dict = (PythonDictionary)this.Retrieve(dictPtr);
            return dict.__len__();
        }
        
        public override IntPtr
        PyDict_GetItemString(IntPtr dictPtr, string key)
        {
            PythonDictionary dict = (PythonDictionary)this.Retrieve(dictPtr);
            if (dict.has_key(key))
            {
                IntPtr result = this.Store(dict[key]);
                this.RememberTempObject(result);
                return result;
            }
            return IntPtr.Zero;
        }

        public override int
        PyDict_SetItem(IntPtr dictPtr, IntPtr keyPtr, IntPtr itemPtr)
        {
            try
            {
                PythonDictionary dict = (PythonDictionary)this.Retrieve(dictPtr);
                dict[this.Retrieve(keyPtr)] = this.Retrieve(itemPtr);
                return 0;
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
            PythonDictionary dict = (PythonDictionary)this.Retrieve(dictPtr);
            dict[key] = this.Retrieve(itemPtr);
            return 0;
        }
    }
}