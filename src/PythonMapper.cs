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
            
            
                default:
                    return IntPtr.Zero;
            }
            return Marshal.GetFunctionPointerForDelegate(this.map[name]);
        }
    }


}