using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;

namespace JumPy
{

    public class PythonMapper
    {
        private Dictionary<string, Delegate> map = new Dictionary<string, Delegate>();
    
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate IntPtr Py_InitModule4_Delegate(string name, IntPtr methods, string doc, IntPtr self, int apiver);
        public virtual IntPtr Py_InitModule4(string name, IntPtr methods, string doc, IntPtr self, int apiver)
        {
            return IntPtr.Zero;
        }
        
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate IntPtr PyString_FromString_Delegate(string text);
        public virtual IntPtr PyString_FromString(string text)
        {
            return IntPtr.Zero;
        }
        
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate int PyModule_AddObject_Delegate(IntPtr module, string name, IntPtr item);
        public virtual int PyModule_AddObject(IntPtr module, string name, IntPtr item)
        {
            return 0;
        }
        
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate int PyArg_ParseTupleAndKeywords_Delegate(IntPtr args, IntPtr kwargs, string format, IntPtr kwlist, IntPtr argPtr);
        public virtual int PyArg_ParseTupleAndKeywords(IntPtr args, IntPtr kwargs, string format, IntPtr kwlist, IntPtr argPtr)
        {
            return 0;
        }
        
        public IntPtr GetAddress(string name)
        {
            if (this.map.ContainsKey(name))
            {
                return Marshal.GetFunctionPointerForDelegate(this.map[name]);
            }
        
            switch (name)
            {
                case "Py_InitModule4":
                    this.map[name] = new Py_InitModule4_Delegate(this.Py_InitModule4);
                    break;
                case "PyString_FromString":
                    this.map[name] = new PyString_FromString_Delegate(this.PyString_FromString);
                    break;
                case "PyModule_AddObject":
                    this.map[name] = new PyModule_AddObject_Delegate(this.PyModule_AddObject);
                    break;
                case "PyArg_ParseTupleAndKeywords":
                    this.map[name] = new PyArg_ParseTupleAndKeywords_Delegate(this.PyArg_ParseTupleAndKeywords);
                    break;
            
            
                default:
                    return IntPtr.Zero;
            }
            return Marshal.GetFunctionPointerForDelegate(this.map[name]);
        }
    }


}