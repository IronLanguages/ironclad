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
        
        
        [DllImport("msvcrt.dll")]
        public static extern IntPtr memcpy(IntPtr dst, IntPtr src, uint bytes);
        
        
        // All these are here because I can't DllImport from msvcr90.dll (sxs issues)
        // They're prefixed IC_ because I can't be bothered to set up a .def to use their real names and forward them
        
        [DllImport("ic_msvcr90.dll")]
        private static extern IntPtr IC__fdopen(int fd, string mode);
        public static IntPtr _fdopen(int fd, string mode) { return IC__fdopen(fd, mode); }
        
        [DllImport("ic_msvcr90.dll")]
        private static extern int IC__open_osfhandle(IntPtr f, int flags);
        public static int _open_osfhandle(IntPtr f, int flags) { return IC__open_osfhandle(f, flags); }
        
        [DllImport("ic_msvcr90.dll")]
        private static extern int IC_fread(IntPtr buf, int size, int count, IntPtr file);
        public static int fread(IntPtr buf, int size, int count, IntPtr file) { return IC_fread(buf, size, count, file); }
        
        [DllImport("ic_msvcr90.dll")]
        private static extern int IC_fwrite(IntPtr buf, int size, int count, IntPtr file);
        public static int fwrite(IntPtr buf, int size, int count, IntPtr file) { return IC_fwrite(buf, size, count, file); }

        [DllImport("ic_msvcr90.dll")]
        private static extern int IC_fflush(IntPtr file);
        public static int fflush(IntPtr file) { return IC_fflush(file); }
        
        [DllImport("ic_msvcr90.dll")]
        private static extern int IC_fclose(IntPtr file);
        public static int fclose(IntPtr file) { return IC_fclose(file); }
        
    }
}
