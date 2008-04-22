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
            
            this.StoreUnmanagedData(dictPtr, dictMgd);
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
    }
}