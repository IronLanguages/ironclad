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

        [DllImport("kernel32.dll")]
        public static extern uint GetLastError();
        

        [DllImport("kernel32.dll")]
        public static extern IntPtr CreateMutex(IntPtr lpMutexAttributes, int bInitialOwner, IntPtr lpName);
        
        [DllImport("kernel32.dll")]
        public static extern int WaitForSingleObject(IntPtr hHandle, int dwMilliseconds);
        
        [DllImport("kernel32.dll")]
        public static extern int ReleaseMutex(IntPtr hMutex);
        
        [DllImport("kernel32.dll")]
        public static extern int CloseHandle(IntPtr hObject);
        
        [DllImport("kernel32.dll")]
        public static extern void DebugBreak();


        [DllImport("msvcr100.dll")]
        public static extern IntPtr _fdopen(int fd, string mode);
    
        [DllImport("msvcr100.dll")]
        public static extern int _open_osfhandle(IntPtr osFileHandle, int flags);

        [DllImport("msvcr100.dll")]
        public static extern nuint fread(IntPtr buf, nuint size, nuint count, IntPtr file);

        [DllImport("msvcr100.dll")]
        public static extern nuint fwrite(IntPtr buf, nuint size, nuint count, IntPtr file);

        [DllImport("msvcr100.dll")]
        public static extern int fflush(IntPtr file);

        [DllImport("msvcr100.dll")]
        public static extern int fclose(IntPtr file);
    }
}
