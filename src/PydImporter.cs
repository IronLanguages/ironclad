
using System;
using System.IO;
using System.Runtime.InteropServices;

namespace JumPy
{
    
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate void PydInit_Delegate();


    public class PydImporter
    {
        [DllImport("kernel32.dll")]
        public static extern IntPtr LoadLibrary(string s);
        
        [DllImport("kernel32.dll")]
        public static extern IntPtr GetProcAddress(IntPtr l, string s);
        
        public void load(string path)
        {
            IntPtr l = LoadLibrary(path);
            string funcName = "init" + Path.GetFileNameWithoutExtension(path);
            IntPtr funcPtr = GetProcAddress(l, funcName);
            PydInit_Delegate d = (PydInit_Delegate)Marshal.GetDelegateForFunctionPointer(funcPtr, typeof(PydInit_Delegate));
            d();
        }
    
    }


}