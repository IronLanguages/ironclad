using System;
using System.IO;
using System.Reflection;
using System.Runtime.InteropServices;

using IronPython.Runtime;

namespace Ironclad
{
    public partial class Python25Mapper : PythonMapper
    {
        // TODO: implement PyFile_Dealloc to call fclose, instead of dirtying up PyObject_Free
        
        public override IntPtr PyFile_AsFile(IntPtr pyFilePtr)
        {
            if (this.FILEs.ContainsKey(pyFilePtr))
            {
                return this.FILEs[pyFilePtr];
            }
            
            PythonFile pyFile = (PythonFile)this.Retrieve(pyFilePtr);
            FieldInfo streamField = (FieldInfo)(pyFile.GetType().GetMember(
                "_stream", BindingFlags.NonPublic | BindingFlags.Instance)[0]);
            FileStream stream = (FileStream)streamField.GetValue(pyFile);
            SafeHandle safeHandle = stream.SafeFileHandle;
            IntPtr handle = safeHandle.DangerousGetHandle();
            
            int fd = Unmanaged._open_osfhandle(handle, 0);
            IntPtr FILE = IntPtr.Zero;
            if (stream.CanWrite)
            {
                FILE = Unmanaged._fdopen(fd, "w");
            }
            else
            {
                FILE = Unmanaged._fdopen(fd, "r");
            }
            this.FILEs[pyFilePtr] = FILE;
            return FILE;
        }        
    }

}
