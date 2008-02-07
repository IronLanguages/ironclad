using System;
using System.Runtime.InteropServices;


namespace JumPy
{
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate IntPtr AddressGetterDelegate(string name);
    
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate void DataSetterDelegate(string name, IntPtr address);
    
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate void InitDelegate(IntPtr addressGetter, IntPtr dataSetter);

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
    
        public void Init(AddressGetterDelegate addressGetter, DataSetterDelegate dataSetter)
        {
            IntPtr initFP = GetProcAddress(this.library, "init");
            InitDelegate initDgt = (InitDelegate)Marshal.GetDelegateForFunctionPointer(initFP, typeof(InitDelegate));
            
            IntPtr addressGetterFP = Marshal.GetFunctionPointerForDelegate(addressGetter);
            IntPtr dataSetterFP = Marshal.GetFunctionPointerForDelegate(dataSetter);
            initDgt(addressGetterFP, dataSetterFP);
        }
        
        public void Dispose()
        {
            FreeLibrary(this.library);
            this.library = IntPtr.Zero;
        }
    }


}