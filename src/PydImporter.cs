
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
        private List<IntPtr> handles = new List<IntPtr>();
        private bool alive = true;
        
        public void
        Load(string path)
        {
            IntPtr l = Unmanaged.LoadLibrary(path);

            this.handles.Add(l);
            string funcName = "PyInit_" + Path.GetFileNameWithoutExtension(path);
            IntPtr funcPtr = Unmanaged.GetProcAddress(l, funcName);
            if (funcPtr == IntPtr.Zero)
            {
                throw new Exception( 
                    String.Format("Could not find module init function {0} in dll {1}", funcName, path));
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
