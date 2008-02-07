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
        private IntPtr library;
    
        public StubReference(string dllPath)
        {
            this.library = Kernel32.LoadLibrary(dllPath);
        }
    
        public void Init(AddressGetterDelegate addressGetter, DataSetterDelegate dataSetter)
        {
            IntPtr initFP = Kernel32.GetProcAddress(this.library, "init");
            InitDelegate initDgt = (InitDelegate)Marshal.GetDelegateForFunctionPointer(initFP, typeof(InitDelegate));
            
            IntPtr addressGetterFP = Marshal.GetFunctionPointerForDelegate(addressGetter);
            IntPtr dataSetterFP = Marshal.GetFunctionPointerForDelegate(dataSetter);
            initDgt(addressGetterFP, dataSetterFP);
        }
        
        public void Dispose()
        {
            Kernel32.FreeLibrary(this.library);
            this.library = IntPtr.Zero;
        }
    }


}