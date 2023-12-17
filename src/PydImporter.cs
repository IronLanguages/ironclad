
using System;
using System.IO;
using System.Collections.Generic;
using System.Runtime.InteropServices;

namespace Ironclad
{
    
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate void PydInit_Delegate();


    public class PydImporter : IDisposable
     {
#if WINDOWS
        public const string PydExtension = ".pyd";
#elif LINUX
  #if ANACONDA
        public const string PydExtension = ".cpython-34m.so";
  #else
        public const string PydExtension = ".cpython-34-x86_64-linux-gnu.so";
  #endif
#else
    #error Unsupported OS platform
#endif

        private List<IntPtr> handles = new List<IntPtr>();
        private bool alive = true;
        
        public void
        Load(string path)
        {
            IntPtr l = Unmanaged.LoadLibrary(path);
            this.handles.Add(l);

            string libname = Path.GetFileName(path);
            if (libname.EndsWith(PydExtension))
            {
                libname = libname.Substring(0, libname.Length - PydExtension.Length);
            }
            string funcName = "PyInit_" + libname;
            IntPtr funcPtr = Unmanaged.GetProcAddress(l, funcName);
            if (funcPtr == IntPtr.Zero)
            {
                throw new Exception( 
                    String.Format("Could not find module init function {0} in PYD {1}", funcName, libname));
            }

            PydInit_Delegate initmodule = (PydInit_Delegate)Marshal.GetDelegateForFunctionPointer(
                funcPtr, typeof(PydInit_Delegate));
            initmodule();
        }
        
        ~PydImporter()
        {
            this.Dispose(false);
        }
        
        protected virtual void
        Dispose(bool disposing)
        {
            if (this.alive)
            {
                this.alive = false;
                foreach (IntPtr l in this.handles)
                {
                    Unmanaged.FreeLibrary(l);
                }
                this.handles.Clear();
            }
        }
        
        public void
        Dispose()
        {
            GC.SuppressFinalize(this);
            this.Dispose(true);
        }
    }
}
