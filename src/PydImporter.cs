
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
        
        public void Load(string path)
        {
            IntPtr l = Unmanaged.LoadLibrary(path);
            this.handles.Add(l);
            string funcName = "init" + Path.GetFileNameWithoutExtension(path);
            IntPtr funcPtr = Unmanaged.GetProcAddress(l, funcName);
            PydInit_Delegate d = (PydInit_Delegate)Marshal.GetDelegateForFunctionPointer(funcPtr, typeof(PydInit_Delegate));
            d();
        }
        
        ~PydImporter()
        {
            this.Dispose(false);
        }
        
        protected virtual void Dispose(bool disposing)
        {
            if (this.alive)
            {
                foreach (IntPtr l in this.handles)
                {
                    Unmanaged.FreeLibrary(l);
                }
                this.handles.Clear();
                this.alive = false;
            }
        }
        
        public void Dispose()
        {
            this.Dispose(true);
            GC.SuppressFinalize(this);
        }
    }
}