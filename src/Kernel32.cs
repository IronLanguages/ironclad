using System;
using System.Runtime.InteropServices;

namespace Ironclad
{
    public class Kernel32
    {
        [DllImport("kernel32.dll")]
        public static extern IntPtr LoadLibrary(string s);
        [DllImport("kernel32.dll")]
        public static extern bool FreeLibrary(IntPtr l);
        [DllImport("kernel32.dll")]
        public static extern IntPtr GetProcAddress(IntPtr l, string s);
        [DllImport("kernel32.dll")]
        public static extern IntPtr GetModuleHandle(string s);
    
    }

}