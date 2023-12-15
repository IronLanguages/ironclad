using System;
using System.IO;
using System.Numerics;
using System.Runtime.InteropServices;
using IronPython.Modules;

namespace Ironclad
{
    public class Unmanaged
    {
#if WINDOWS
        /// <summary>
        /// Load a DLL library into the process memory space and return its handle.
        /// </summary>
        /// <param name="dllPath">The path to the DLL file to load.</param>
        /// <returns>Handle of the library in memory. Never null if no exception thrown.</returns>
        /// <exception cref="Exception">OSError if loading of the library failed.</exception>
        public static IntPtr LoadLibrary(string dllPath)
        {
            // according to MSDN, LoadLibrary requires "\"
            dllPath = dllPath.Replace("/", @"\");
            return FromPythonInt(CTypes.LoadLibrary(dllPath));
        }

        public static void FreeLibrary(IntPtr handle)
            => CTypes.FreeLibrary(handle);

        [DllImport("kernel32.dll")]
        public static extern IntPtr GetProcAddress(IntPtr handle, string funcName);

        [DllImport("kernel32.dll")]
        public static extern IntPtr GetModuleHandle(string s); // For testing purposes only


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


#endif

        private static IntPtr FromPythonInt(object o)
        {
            return o switch
            {
                int i => new IntPtr(i),
                BigInteger bi => new IntPtr(checked((long)bi)),
                _ => throw new InvalidCastException()
            };
        }
    }
}
