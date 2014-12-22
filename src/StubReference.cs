using System;
using System.Runtime.InteropServices;


namespace Ironclad
{
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate IntPtr dgt_getfuncptr(string name);
    
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate void dgt_registerdata(string name, IntPtr address);
    
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate void InitDelegate(IntPtr addressGetter, IntPtr dataSetter);

    public class StubReference : IDisposable
    {
        private IntPtr library;
        private bool alive = true;
    
        public StubReference(string dllPath)
        {
            // according to MSDN, LoadLibrary requires "\"
            dllPath = dllPath.Replace("/", @"\");
            this.library = Unmanaged.LoadLibrary(dllPath);
            if (this.library == IntPtr.Zero)
            {
                throw new Exception(
                    String.Format("Could not load library '{0}' . Error code:{1}", dllPath, Unmanaged.GetLastError()));
            }
        }
        
        ~StubReference()
        {
            this.Dispose(false);
        }
    
        public void
        Init(dgt_getfuncptr addressGetter, dgt_registerdata dataSetter)
        {
            IntPtr initFP = Unmanaged.GetProcAddress(this.library, "init");
            InitDelegate initDgt = (InitDelegate)Marshal.GetDelegateForFunctionPointer(initFP, typeof(InitDelegate));
            
            IntPtr addressGetterFP = Marshal.GetFunctionPointerForDelegate(addressGetter);
            IntPtr dataSetterFP = Marshal.GetFunctionPointerForDelegate(dataSetter);
            initDgt(addressGetterFP, dataSetterFP);
            
            // yes, these do appear to be necessary: rare NullReferenceExceptions will be thrown
            // from the initDgt call otherwise. run functionalitytest in a loop to observe.
            GC.KeepAlive(addressGetter);
            GC.KeepAlive(dataSetter);
        }
        
        public void
        LoadBuiltinModule(string name)
        {
            IntPtr initFP = Unmanaged.GetProcAddress(this.library, "init" + name);
            PydInit_Delegate init = (PydInit_Delegate)Marshal.GetDelegateForFunctionPointer(initFP, typeof(PydInit_Delegate));
            init();
        }
        
        protected virtual void
        Dispose(bool disposing)
        {
            if (this.alive)
            {
                Unmanaged.FreeLibrary(this.library);
                this.library = IntPtr.Zero;
                this.alive = false;
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
