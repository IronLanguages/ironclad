
using System;
using System.IO;
using System.Collections.Generic;
using System.Runtime.InteropServices;

namespace Ironclad
{
    
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate void PydInit_Delegate();


    public class PydImporter
    {
        private List<IntPtr> handles;
        
        public PydImporter()
        {
            this.handles = new List<IntPtr>();
        }
        
        public void Load(string path)
        {
            IntPtr l = Unmanaged.LoadLibrary(path);
            this.handles.Add(l);
            string funcName = "init" + Path.GetFileNameWithoutExtension(path);
            IntPtr funcPtr = Unmanaged.GetProcAddress(l, funcName);
            PydInit_Delegate d = (PydInit_Delegate)Marshal.GetDelegateForFunctionPointer(funcPtr, typeof(PydInit_Delegate));
            d();
        }
        
        public void Dispose()
        {
            foreach (IntPtr l in this.handles)
            {
                Unmanaged.FreeLibrary(l);
            }
        }
    }


}