using System;
using System.Runtime.InteropServices;

using IronPython.Runtime;
using Ironclad.Structs;

namespace Ironclad
{
    public partial class Python25Mapper : PythonMapper
    {
        
        public override IntPtr
        PyDict_New()
        {
            return this.Store(new Dict());
        }
        
        private IntPtr
        Store(Dict dictMgd)
        {
            PyObject dict = new PyObject();
            dict.ob_refcnt = 1;
            dict.ob_type = this.PyDict_Type;
            IntPtr dictPtr = this.allocator.Alloc(Marshal.SizeOf(typeof(PyObject)));
            Marshal.StructureToPtr(dict, dictPtr, false);
            
            this.StoreUnmanagedData(dictPtr, dictMgd);
            return dictPtr;
        }
        
        public override int
        PyDict_Size(IntPtr dictPtr)
        {
            Dict dict = (Dict)this.Retrieve(dictPtr);
            return dict.Count;
        }
        
        public override IntPtr
        PyDict_GetItemString(IntPtr dictPtr, string key)
        {
            Dict dict = (Dict)this.Retrieve(dictPtr);
            if (dict.ContainsKey(key))
            {
                IntPtr result = this.Store(dict[key]);
                this.RememberTempObject(result);
                return result;
            }
            return IntPtr.Zero;
        }
    }
}