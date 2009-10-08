
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
            // the ActCtx stuff allows us to import .pyds which link to msvcr90 but don't have manifests
            // implementation explained in stub/ic_msvcr90.c
            IntPtr cookie = Unmanaged._Py_ActivateActCtx();
            IntPtr l = Unmanaged.LoadLibrary(path);
            Unmanaged._Py_DeactivateActCtx(cookie);
            
            if (l == IntPtr.Zero)
            {
                throw new Exception(
                    String.Format("Could not load library '{0}' . Error code:{1}", path, Unmanaged.GetLastError()));
            }

            this.handles.Add(l);
            string funcName = "init" + Path.GetFileNameWithoutExtension(path);
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