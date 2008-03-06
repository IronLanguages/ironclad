using System;
using System.Runtime.InteropServices;

namespace Ironclad
{
    public class Unmanaged
    {
        [DllImport("kernel32.dll")]
        public static extern IntPtr LoadLibrary(string s);
        
        [DllImport("kernel32.dll")]
        public static extern bool FreeLibrary(IntPtr l);
        
        [DllImport("kernel32.dll")]
        public static extern IntPtr GetProcAddress(IntPtr l, string s);
        
        [DllImport("kernel32.dll")]
        public static extern IntPtr GetModuleHandle(string s);
        
        [DllImport("msvcrt.dll")]
        public static extern IntPtr _fdopen(int fd, string mode);
        
        [DllImport("msvcrt.dll")]
        public static extern int _open_osfhandle(IntPtr f, int flags);
    }
}