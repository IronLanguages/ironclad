using System;
using System.Runtime.InteropServices;


namespace JumPy
{
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate IntPtr AddressGetterDelegate(string name);
    
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate void InitDelegate(IntPtr addressGetter);

    public class StubReference
    {
        [DllImport("kernel32.dll")]
        public static extern IntPtr GetModuleHandle(string s);
        
        private IntPtr library;
        
        [DllImport("kernel32.dll")]
        private static extern IntPtr LoadLibrary(string s);
        [DllImport("kernel32.dll")]
        private static extern IntPtr GetProcAddress(IntPtr l, string s);
        [DllImport("kernel32.dll")]
        private static extern bool FreeLibrary(IntPtr l);
    
        public StubReference(string dllPath)
        {
            this.library = LoadLibrary(dllPath);
        }
    
        public void Init(AddressGetterDelegate d)
        {
            IntPtr initFP = GetProcAddress(this.library, "init");
            InitDelegate initDgt = (InitDelegate)Marshal.GetDelegateForFunctionPointer(initFP, typeof(InitDelegate));
            IntPtr addressGetterFP = Marshal.GetFunctionPointerForDelegate(d);
            initDgt(addressGetterFP);
        }
        
        public void Dispose()
        {
            FreeLibrary(this.library);
            this.library = IntPtr.Zero;
        }
    }


}